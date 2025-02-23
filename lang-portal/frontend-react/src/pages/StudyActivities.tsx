import { useEffect, useState } from 'react'
import StudyActivity from '@/components/StudyActivity'
import { StudyActivity as ActivityType, fetchStudyActivities } from '@/services/api'

export default function StudyActivities() {
  const [activities, setActivities] = useState<ActivityType[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchStudyActivities()
      .then(data => {
        console.log("Fetched activities:", data)
        setActivities(data)
        setLoading(false)
      })
      .catch(err => {
        console.error("Error fetching activities:", err)
        setError(err.message)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error: {error}</div>
  }

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">Study Activities</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {activities.map(activity => (
          <StudyActivity key={activity.id} activity={activity} />
        ))}
      </div>
    </div>
  )
}