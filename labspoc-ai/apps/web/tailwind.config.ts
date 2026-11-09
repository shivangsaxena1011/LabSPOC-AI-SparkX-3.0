import type { Config } from "tailwindcss";
const config: Config = { content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"], theme: { extend: { colors: { ink:"#101828", muted:"#667085", line:"#E6EAF0", brand:"#3157D5", teal:"#0F766E" } } }, plugins: [] };
export default config;
