const paths: Record<string, string> = {
  home: 'M3 11.5 12 4l9 7.5V21h-6v-6H9v6H3z',
  inspections: 'M4 5h16v14H4z M8 2v6 M16 2v6 M7 15l3-3 3 3 2-2 3 3',
  assistant: 'M4 5h16v12H8l-4 4z M8 9h8 M8 13h5',
  device: 'M8 2h8a3 3 0 0 1 3 3v14a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V5a3 3 0 0 1 3-3z M9 6h6 M10 18h4',
  settings: 'M12 8.5A3.5 3.5 0 1 0 12 15.5 3.5 3.5 0 0 0 12 8.5z M4 12H2m20 0h-2M12 4V2m0 20v-2M6.3 6.3 4.9 4.9m14.2 14.2-1.4-1.4M17.7 6.3l1.4-1.4M4.9 19.1l1.4-1.4',
  camera: 'M4 7h4l2-3h4l2 3h4v12H4z M12 10a4 4 0 1 0 0 8 4 4 0 0 0 0-8z',
  mic: 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3z M5 11a7 7 0 0 0 14 0 M12 18v4 M8 22h8',
  battery: 'M3 7h17v10H3z M20 10h2v4h-2',
  storage: 'M5 3h12l2 2v16H5z M8 3v6h8V3 M9 17h6',
  signal: 'M4 17h2v3H4z M9 13h2v7H9z M14 9h2v11h-2z M19 4h2v16h-2z',
  refresh: 'M20 11a8 8 0 1 0-2.3 5.7 M20 5v6h-6',
  search: 'M10.5 4a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13z M15.5 15.5 21 21',
  download: 'M12 3v12 M7 10l5 5 5-5 M4 21h16',
  chevron: 'm9 5 7 7-7 7',
  close: 'M5 5l14 14M19 5 5 19',
  shield: 'M12 2 20 5v6c0 5-3.4 9-8 11-4.6-2-8-6-8-11V5z M8 12l2.5 2.5L16 9',
  alert: 'M12 3 2 21h20z M12 9v5 M12 18h.01',
}

export function Icon({ name, size = 20 }: { name: keyof typeof paths; size?: number }) {
  return <svg className="icon" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>
}
