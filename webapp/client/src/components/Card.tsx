import React from 'react';
import { CardText } from './CardText';

export interface cardData {
    sentence_id: number;
    sentence: string[];
    translated_sentence: string[];
    img_url: string;
}

interface Props {
    card?: cardData;
    is_flipped: boolean;
    clicked_words: number[];
    updateClicked: (index: number) => void;
}

export const Card: React.FC<Props> = ({ card, is_flipped, clicked_words, updateClicked }) => {
    return (
        <div className="flex w-full items-center overflow-x-scroll rounded-lg shadow-2xl bg-violet-100">
            <img className="w-4/12 ml-12 rounded-lg" src={card?.img_url} alt="img" />
            <CardText sentence={is_flipped ? card?.translated_sentence : card?.sentence} is_flipped={is_flipped} clicked_words={clicked_words} updateClicked={updateClicked}/>
        </div>
    );
}
