import React from 'react';

export const DoneModal: React.FC = () => {
    return (
		<div className="fixed top-0 left-0 w-full h-full bg-gray-900 bg-opacity-75 flex justify-center items-center">
			<div className="flex flex-col justify-center items-center w-1/6 h-1/6 bg-violet-900 rounded-lg shadow-lg p-8">
                <h1 className="text-3xl">Done</h1>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" className="w-10 h-10">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p>Log back in tomorrow!</p>
			</div>
		</div>
    );
}