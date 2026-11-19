// KH: tests for the cookbook export's ZIP writer and file names (D61): signatures, sizes, CRC and the central directory
// as a reader checks them, UTF-8 names, and the names made safe and unique.
import { describe, expect, test } from "vitest";
import { crc32, makeZip, safeFileName, uniqueNames } from "../lib/zip";

const text = (value: string) => new TextEncoder().encode(value);

describe("crc32", () => {
  test("the standard check value", () => {
    expect(crc32(text("123456789"))).toBe(0xCBF43926);
  });
  test("empty data", () => {
    expect(crc32(new Uint8Array())).toBe(0);
  });
});

describe("makeZip", () => {
  const zip = makeZip([
    { name: "Buch/Käse.txt", data: text("123456789") },
    { name: "Buch/Brot.txt", data: text("Brot") },
  ]);
  const view = new DataView(zip.buffer);
  const end = zip.length - 22;

  test("ends with the central directory's end record counting both files", () => {
    expect(view.getUint32(end, true)).toBe(0x06054B50);
    expect(view.getUint16(end + 8, true)).toBe(2);
    expect(view.getUint16(end + 10, true)).toBe(2);
    expect(view.getUint32(end + 16, true) + view.getUint32(end + 12, true)).toBe(end);
  });
  test("first local entry: signature, UTF-8 flag, stored, CRC, sizes and the name", () => {
    expect(view.getUint32(0, true)).toBe(0x04034B50);
    expect(view.getUint16(6, true) & 0x0800).toBe(0x0800);
    expect(view.getUint16(8, true)).toBe(0);
    expect(view.getUint32(14, true)).toBe(0xCBF43926);
    expect(view.getUint32(18, true)).toBe(9);
    expect(view.getUint32(22, true)).toBe(9);
    const nameLength = view.getUint16(26, true);
    expect(new TextDecoder().decode(zip.slice(30, 30 + nameLength))).toBe("Buch/Käse.txt");
    expect(new TextDecoder().decode(zip.slice(30 + nameLength, 39 + nameLength))).toBe("123456789");
  });
  test("the central directory points at the second local entry", () => {
    const first = view.getUint32(end + 16, true);
    const firstLength = view.getUint16(first + 28, true);
    const second = first + 46 + firstLength;
    expect(view.getUint32(second, true)).toBe(0x02014B50);
    const offset = view.getUint32(second + 42, true);
    expect(view.getUint32(offset, true)).toBe(0x04034B50);
    expect(view.getUint32(offset + 18, true)).toBe(4);
  });
});

describe("file names", () => {
  test("characters not allowed in file names are dropped and the ends trimmed", () => {
    expect(safeFileName("  Käse/Sahne: \"Torte\"? ")).toBe("KäseSahne Torte");
    expect(safeFileName("a\\b*c<d>e|f.")).toBe("abcdef");
  });
  test("a name with nothing left", () => {
    expect(safeFileName("///")).toBe("Rezept");
  });
  test("doubles get a number, whatever their letter case", () => {
    expect(uniqueNames(["Brot", "Kuchen", "brot", "Brot"])).toEqual(["Brot", "Kuchen", "brot (2)", "Brot (3)"]);
  });
});
