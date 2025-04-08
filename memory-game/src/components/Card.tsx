import './Card.css';
import { Card as CardType } from '../types';

interface CardProps {
  card: CardType;
  onClick: () => void;
}

export const Card = ({ card, onClick }: CardProps) => {
  return (
    <div
      onClick={onClick}
      className={`memory-card ${card.isFlipped ? 'flipped' : ''} ${card.isMatched ? 'matched' : ''}`}
    >
      <div className="card-content">
        {card.isFlipped ? card.word : '?'}
      </div>
    </div>
  );
};
