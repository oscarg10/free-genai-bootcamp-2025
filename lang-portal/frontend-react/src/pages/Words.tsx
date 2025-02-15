import React, { useState, useEffect } from 'react'
import { fetchWords, createWord, type Word } from '../services/api'
import WordsTable, { WordSortKey } from '../components/WordsTable'
import { Button } from '../components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'

export default function Words() {
  const [words, setWords] = useState<Word[]>([])
  const [sortKey, setSortKey] = useState<WordSortKey>('german')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [newWord, setNewWord] = useState<{
    german: string;
    english: string;
    article: string;
    word_type: 'noun' | 'verb' | 'adjective';
    pronunciation: string;
  }>({
    german: '',
    english: '',
    article: '',
    word_type: 'noun',
    pronunciation: '',
  })

  useEffect(() => {
    const loadWords = async () => {
      setIsLoading(true)
      setError(null)
      try {
        const response = await fetchWords(currentPage, undefined, sortKey, sortDirection)
        setWords(response.data.words)
        setTotalPages(response.data.pagination.total_pages)
      } catch (err) {
        setError('Failed to load words')
        console.error(err)
      } finally {
        setIsLoading(false)
      }
    }

    loadWords()
  }, [currentPage, sortKey, sortDirection])

  const handleSort = (key: WordSortKey) => {
    if (key === sortKey) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortKey(key)
      setSortDirection('asc')
    }
  }

  if (isLoading) {
    return <div className="text-center py-4">Loading...</div>
  }

  if (error) {
    return <div className="text-red-500 text-center py-4">{error}</div>
  }

  const handleCreateWord = async () => {
    try {
      await createWord(newWord)
      // Refresh the word list
      const response = await fetchWords(currentPage, undefined, sortKey, sortDirection)
      setWords(response.data.words)
      setTotalPages(response.data.pagination.total_pages)
      // Reset form and close dialog
      setNewWord({
        german: '',
        english: '',
        article: '',
        word_type: 'noun',
        pronunciation: '',
      })
      setIsDialogOpen(false)
    } catch (err) {
      console.error('Failed to create word:', err)
      setError('Failed to create word')
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Words</h1>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button>Create Word</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Word</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="german" className="text-right">German</Label>
                <Input
                  id="german"
                  value={newWord.german}
                  onChange={(e) => setNewWord({ ...newWord, german: e.target.value })}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="english" className="text-right">English</Label>
                <Input
                  id="english"
                  value={newWord.english}
                  onChange={(e) => setNewWord({ ...newWord, english: e.target.value })}
                  className="col-span-3"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="article" className="text-right">Article</Label>
                <Input
                  id="article"
                  value={newWord.article}
                  onChange={(e) => setNewWord({ ...newWord, article: e.target.value })}
                  className="col-span-3"
                  placeholder="der/die/das"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="type" className="text-right">Type</Label>
                <Select
                  value={newWord.word_type}
                  onValueChange={(value: 'noun' | 'verb' | 'adjective') => 
                    setNewWord({ ...newWord, word_type: value })
                  }
                >
                  <SelectTrigger className="col-span-3">
                    <SelectValue placeholder="Select word type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="noun">Noun</SelectItem>
                    <SelectItem value="verb">Verb</SelectItem>
                    <SelectItem value="adjective">Adjective</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="pronunciation" className="text-right">Pronunciation</Label>
                <Input
                  id="pronunciation"
                  value={newWord.pronunciation}
                  onChange={(e) => setNewWord({ ...newWord, pronunciation: e.target.value })}
                  className="col-span-3"
                />
              </div>
            </div>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleCreateWord}>Create</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
      
      <WordsTable 
        words={words}
        sortKey={sortKey}
        sortDirection={sortDirection}
        onSort={handleSort}
      />

      <div className="flex justify-center space-x-2">
        <button
          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
          disabled={currentPage === 1}
          className="px-4 py-2 border rounded-md bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          Previous
        </button>
        <span className="px-4 py-2 text-gray-800 dark:text-gray-200">
          Page {currentPage} of {totalPages}
        </span>
        <button
          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
          disabled={currentPage === totalPages}
          className="px-4 py-2 border rounded-md bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-300 dark:border-gray-600 disabled:opacity-50 hover:bg-gray-50 dark:hover:bg-gray-700"
        >
          Next
        </button>
      </div>
    </div>
  )
}