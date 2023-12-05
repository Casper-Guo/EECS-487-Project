import React from 'react';
import { CardWord } from './CardWord';

const formatText = (sentence: string[] = [], is_flipped: boolean, clicked_words: number[], updateClicked: (index: number) => void): JSX.Element[] => {
    let formatted_text: JSX.Element[] = [];

    console.log(clicked_words)

    for (let i = 0; i < sentence.length; i++) {
        formatted_text.push(<CardWord key={i} index={i} word={sentence[i]} is_flipped={is_flipped} clicked={clicked_words.includes(i)} updateClicked={updateClicked}/>);
    }

    return formatted_text;
}

interface Props {
    sentence?: string[];
    is_flipped: boolean;
    clicked_words: number[];
    updateClicked: (index: number) => void;
}

export const CardText: React.FC<Props> = ({ sentence, is_flipped, clicked_words, updateClicked }) => {
    return (
        <p className="text-5xl md:text-5xl text-black m-auto select-none">
            {formatText(sentence, is_flipped, clicked_words, updateClicked)}
        </p>
    );
};
