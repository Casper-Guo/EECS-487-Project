import React from 'react'

export const Navbar: React.FC = () => {
    return (
        <header className="flex shadow-lg w-full sticky items-center justify-center align-middle py-4 text-4xl rounded-b-lg bg-violet-100 text-black">
            <a href="/" className="text-xs"><img src="/maestro.svg" alt="logo"/></a>
                &nbsp;
            <a href="/">Maestro<sub className="text-xs"></sub></a>
        </header>
    );
};
