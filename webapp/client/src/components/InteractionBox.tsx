import React from 'react';

interface Props {
    onFlip: (flip: boolean, time: number) => void;
    is_flipped: boolean;
    onNext: () => void;
}

export const InteractionBox: React.FC<Props> = ({ onFlip, is_flipped, onNext }) => {
    // is flipped is state to decide what to show for the interaction box
    // onFlip is a prop to pass that handles sends data to App and Card when user requests to flip card

    const renderPropmts = () => {
        if (is_flipped) {
            return (
                <>
                    <input type="text" id="input-large" className="w-5/6 p-4 rounded-l-lg cursor-text" disabled/>
                    <div className="w-1/5 flex">
                        <button onClick={onNext} className="flex items-center justify-center w-full m-2 shadow-md rounded-lg bg-violet-500 hover:bg-violet-600 active:bg-violet-700 transition-all duration-300 text-xl">
                            Next Card
                            &nbsp;
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                                <path fillRule="evenodd" d="M2 10a.75.75 0 01.75-.75h12.59l-2.1-1.95a.75.75 0 111.02-1.1l3.5 3.25a.75.75 0 010 1.1l-3.5 3.25a.75.75 0 11-1.02-1.1l2.1-1.95H2.75A.75.75 0 012 10z" clipRule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </>
            );
        }

        return  (
            <>
                <input type="text" id="input-large" className="w-5/6 p-4 rounded-l-lg cursor-text placeholder:text-black placeholder:text-xl placeholder:antialiased" placeholder="Click on the words you do not know" disabled/>
                <div className="w-1/5 flex">
                    <button onClick={() => { onFlip(true, Date.now()) }} className="flex items-center justify-center w-full m-2 shadow-md rounded-lg bg-violet-500 hover:bg-violet-600 active:bg-violet-700 transition-all duration-300 text-xl">
                        Flip Card
                    </button>
                </div>
            </>
        );
    }

    return (
        <div className="flex w-10/12 mt-5 shadow-2xl rounded-lg bg-violet-100">
            {renderPropmts()}
        </div>
    );
}
