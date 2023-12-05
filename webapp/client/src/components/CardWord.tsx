import React, { useState, useEffect } from 'react';


// Target lets us know this word is the new word that is to be highlighted
interface Props {
    index: number;
    word: string;
    is_flipped: boolean;
    clicked: boolean;
    updateClicked: (index: number) => void;
}

export const CardWord: React.FC<Props> = ({ index, word, is_flipped, clicked, updateClicked }) => {
    const [is_clicked, setClick] = useState(clicked);
    useEffect(() => {
        if (is_flipped) {
            setClick(false);
        }
    }, [is_flipped]);

    if (is_flipped) {
        return (
            <span className='cursor-pointer'><button className={"rounded-md px-1 my-1 cursor-pointer"}>{word}</button>&nbsp;</span>
        );
    }
    return (
        <span className='cursor-pointer'><button onClick={() => {setClick(!is_clicked); updateClicked(index)}} className={is_clicked ? "bg-violet-500 hover:bg-violet-600 active:bg-violet-600 rounded-md px-1 my-1 cursor-pointer transition-all duration-300" : "hover:underline hover:decoration-violet-500 cursor-pointer transition-all duration-300"}>{word}</button>&nbsp;</span>
    );
}
