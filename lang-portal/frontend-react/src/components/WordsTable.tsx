import React from 'react'
import { Link } from 'react-router-dom'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { Word } from '../services/api'

export type WordSortKey = 'german' | 'english' | 'word_type' | 'correct_count' | 'wrong_count'

interface WordsTableProps {
  words: Word[]
  sortKey: WordSortKey
  sortDirection: 'asc' | 'desc'
  onSort: (key: WordSortKey) => void
}

export default function WordsTable({ words, sortKey, sortDirection, onSort }: WordsTableProps) {
  const getArticleColor = (article: string) => {
    switch (article) {
      case 'der':
        return 'text-blue-600 dark:text-blue-400'
      case 'die':
        return 'text-red-600 dark:text-red-400'
      case 'das':
        return 'text-green-600 dark:text-green-400'
      default:
        return 'text-gray-600 dark:text-gray-400'
    }
  }

  return (
    <div className="overflow-x-auto bg-white dark:bg-gray-800 rounded-lg shadow">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-900">
          <tr>
            {(['german', 'english', 'word_type', 'correct_count', 'wrong_count'] as const).map((key) => (
              <th
                key={key}
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => onSort(key)}
              >
                <div className="flex items-center space-x-1">
                  <span>
                    {key === 'correct_count' ? 'Correct' :
                     key === 'wrong_count' ? 'Wrong' :
                     key === 'word_type' ? 'Type' :
                     key.charAt(0).toUpperCase() + key.slice(1)}
                  </span>
                  {sortKey === key && (
                    sortDirection === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                  )}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200 dark:bg-gray-800 dark:divide-gray-700">
          {words.map((word) => (
            <tr key={word.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
              <td className="px-6 py-4 whitespace-nowrap">
                <Link
                  to={`/words/${word.id}`}
                  className="flex items-center space-x-2"
                >
                  {word.word_type === 'noun' && (
                    <span className={`${getArticleColor(word.article)} font-medium`}>
                      {word.article}
                    </span>
                  )}
                  <span className="text-blue-600 dark:text-blue-400 hover:underline">
                    {word.german}
                  </span>
                  {word.word_type === 'noun' && word.additional_info?.plural && (
                    <span className="text-gray-500 dark:text-gray-400 text-sm">
                      ({word.additional_info.plural})
                    </span>
                  )}
                  {word.word_type === 'adjective' && (
                    <span className="text-gray-500 dark:text-gray-400 text-sm">
                      {word.additional_info?.comparative && `(${word.additional_info.comparative}, `}
                      {word.additional_info?.superlative && `${word.additional_info.superlative})`}
                    </span>
                  )}
                </Link>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-gray-500 dark:text-gray-400">
                {word.english}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <span className={`px-2 py-1 text-xs font-medium rounded-full
                  ${word.word_type === 'noun' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
                    word.word_type === 'verb' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' :
                    'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'}`}>
                  {word.word_type}
                </span>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-green-600 dark:text-green-400">
                {word.correct_count}
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-red-600 dark:text-red-400">
                {word.wrong_count}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
