/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ["var(--font-inter)"],
                outfit: ["var(--font-outfit)"],
                mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "monospace"],
            },
            colors: {
                background: "rgb(var(--background))",
                foreground: "rgb(var(--foreground))",
            },
        },
    },
    plugins: [],
};
