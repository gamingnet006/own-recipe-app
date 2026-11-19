// KH: a minimal ZIP writer for the cookbook export (D61): store method only (no compression), CRC-32, UTF-8 names. It
// saves a dependency; text and photos hardly shrink for a family cookbook, and a ZIP is limited to 65535 files / 4 GB.

export interface ZipEntry {
  name: string;
  data: Uint8Array;
}

const CRC_TABLE = Array.from({ length: 256 }, (_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
  return c >>> 0;
});

/** The CRC-32 of DATA as ZIP stores it ("123456789" gives 0xCBF43926). */
export function crc32(data: Uint8Array): number {
  let crc = 0xFFFFFFFF;
  for (const byte of data) crc = CRC_TABLE[(crc ^ byte) & 0xFF]! ^ (crc >>> 8);
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

/** The ZIP of ENTRIES, in order. Names are UTF-8 (general purpose flag bit 11), so umlauts survive. */
export function makeZip(entries: ZipEntry[], now = new Date()): Uint8Array<ArrayBuffer> {
  const encoder = new TextEncoder();
  const time = (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
  const date = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();
  const parts: Uint8Array[] = [];
  const central: Uint8Array[] = [];
  let offset = 0;
  for (const { name, data } of entries) {
    const nameBytes = encoder.encode(name);
    const crc = crc32(data);
    const local = new DataView(new ArrayBuffer(30));
    local.setUint32(0, 0x04034B50, true);
    local.setUint16(4, 20, true); // version needed
    local.setUint16(6, 0x0800, true); // UTF-8 names
    local.setUint16(10, time, true); // the method at 8 stays 0: stored
    local.setUint16(12, date, true);
    local.setUint32(14, crc, true);
    local.setUint32(18, data.length, true);
    local.setUint32(22, data.length, true);
    local.setUint16(26, nameBytes.length, true);
    const entry = new DataView(new ArrayBuffer(46));
    entry.setUint32(0, 0x02014B50, true);
    entry.setUint16(4, 20, true); // version made by
    entry.setUint16(6, 20, true); // version needed
    entry.setUint16(8, 0x0800, true);
    entry.setUint16(12, time, true);
    entry.setUint16(14, date, true);
    entry.setUint32(16, crc, true);
    entry.setUint32(20, data.length, true);
    entry.setUint32(24, data.length, true);
    entry.setUint16(28, nameBytes.length, true);
    entry.setUint32(42, offset, true);
    parts.push(new Uint8Array(local.buffer), nameBytes, data);
    central.push(new Uint8Array(entry.buffer), nameBytes);
    offset += 30 + nameBytes.length + data.length;
  }
  const centralSize = central.reduce((sum, part) => sum + part.length, 0);
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054B50, true);
  end.setUint16(8, entries.length, true);
  end.setUint16(10, entries.length, true);
  end.setUint32(12, centralSize, true);
  end.setUint32(16, offset, true);
  const all = [...parts, ...central, new Uint8Array(end.buffer)];
  const zip = new Uint8Array(all.reduce((sum, part) => sum + part.length, 0));
  let at = 0;
  for (const part of all) {
    zip.set(part, at);
    at += part.length;
  }
  return zip;
}

/** NAME as a file name: characters Windows and macOS refuse (/ \ : * ? " < > |) and control characters are dropped, the
 * ends trimmed (a name may not end in a dot either); "Rezept" when nothing is left. */
export function safeFileName(name: string): string {
  // eslint-disable-next-line no-control-regex
  const clean = name.replace(/[/\\:*?"<>|\u0000-\u001F]/g, "").trim().replace(/\.+$/, "").trim();
  return clean || "Rezept";
}

/** The names with doubles told apart: "Name", "Name (2)", "Name (3)" (letter case does not count, macOS ignores it). */
export function uniqueNames(names: string[]): string[] {
  const used = new Set<string>();
  return names.map((name) => {
    let candidate = name;
    for (let n = 2; used.has(candidate.toLowerCase()); n++) candidate = `${name} (${n})`;
    used.add(candidate.toLowerCase());
    return candidate;
  });
}
