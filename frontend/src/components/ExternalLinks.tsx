import React from 'react';

interface ExternalLinksProps {
  selectedTicker: string;
}

const ExternalLinks: React.FC<ExternalLinksProps> = ({ selectedTicker }) => {
  const links = [
    { name: 'Yahoo', url: `https://finance.yahoo.com/quote/${selectedTicker}/` },
    { name: 'Finviz', url: `https://finviz.com/quote.ashx?t=${selectedTicker}&ty=c&ta=1&p=d` },
  ];

  return (
    <div className="mt-[20px] pt-[15px] border-t border-[#444] space-y-2">
      {links.map((link) => (
        <button
          key={link.name}
          className="w-full py-[8px] bg-[#2d5a8e] text-white border-none rounded cursor-pointer font-bold hover:bg-[#3a6ea8] disabled:bg-[#666] disabled:cursor-not-allowed transition-colors text-sm"
          onClick={() => window.open(link.url, '_blank')}
          disabled={!selectedTicker}
        >
          {link.name}
        </button>
      ))}
    </div>
  );
};

export default ExternalLinks;
