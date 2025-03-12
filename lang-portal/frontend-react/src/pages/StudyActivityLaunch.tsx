import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Button } from "@/components/ui/button"
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select"
import { useNavigation } from '@/context/NavigationContext'
import { createStudySession } from '@/services/api'

type Group = {
    id: number
    name: string
}

type StudyActivity = {
    id: number
    title: string
    launch_url: string
    preview_url: string
    activity_type: 'typing' | 'writing' | 'song' | 'listening'
}

type LaunchData = {
    activity: StudyActivity
    groups?: Group[]
}

export default function StudyActivityLaunch() {
    const { id } = useParams()
    const navigate = useNavigate()
    const { setCurrentStudyActivity } = useNavigation()
    const [launchData, setLaunchData] = useState<LaunchData | null>(null)
    const [selectedGroup, setSelectedGroup] = useState<string>('')
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        fetch(`http://localhost:5100/api/study-activities/${id}/launch`)
            .then(response => {
                if (!response.ok) throw new Error('Failed to fetch launch data')
                return response.json()
            })
            .then(data => {
                setLaunchData(data)
                setCurrentStudyActivity(data.activity)
                setLoading(false)
            })
            .catch(err => {
                setError(err.message)
                setLoading(false)
            })
    }, [id, setCurrentStudyActivity])

    // Clean up when unmounting
    useEffect(() => {
        return () => {
            setCurrentStudyActivity(null)
        }
    }, [setCurrentStudyActivity])

    const handleTypingLaunch = async () => {
        if (!launchData?.activity || !selectedGroup) {
            console.log('Missing data:', { 
                activity: launchData?.activity, 
                selectedGroup 
            });
            return;
        }
        
        try {
            const result = await createStudySession(
                parseInt(selectedGroup), 
                launchData.activity.id
            );
            const sessionId = result.session_id;
            if (!sessionId) {
                console.error('No session ID returned from server');
                return;
            }
            
            // Open typing tutor app with session and group ID
            const appUrl = `${launchData.activity.launch_url}/?` + 
                `session_id=${sessionId}&` +
                `group_id=${selectedGroup}`;
            window.open(appUrl, '_blank');
            
            // Navigate to the session show page
            navigate(`/sessions/${sessionId}`);
        } catch (error) {
            console.error('Failed to launch activity:', error);
            setError(
                error instanceof Error 
                    ? error.message 
                    : 'Failed to launch activity'
            );
        }
    }

    const handleDirectLaunch = async () => {
        if (!launchData?.activity) {
            console.log('Missing activity data:', launchData?.activity);
            return;
        }

        try {
            // For writing practice, create session without group
            if (launchData.activity.activity_type === 'writing') {
                const result = await createStudySession(
                    undefined,
                    launchData.activity.id
                );
                const sessionId = result.session_id;
                if (!sessionId) {
                    console.error('No session ID returned');
                    return;
                }
                // Launch writing practice with session
                const url = `${launchData.activity.launch_url}/?` +
                    `session_id=${sessionId}&` +
                    `group_id=1`; // Use group 1 (Basic German) for writing practice
                window.open(url, '_blank');
            } else {
                // For other activities, just open in new tab
                window.open(launchData.activity.launch_url, '_blank');
            }
        } catch (error) {
            console.error('Failed to launch activity:', error);
            setError(
                error instanceof Error 
                    ? error.message 
                    : 'Failed to launch activity'
            );
        }
    }

    if (loading) {
        return <div className="text-center">Loading...</div>
    }

    if (error) {
        return <div className="text-red-500">Error: {error}</div>
    }

    if (!launchData) {
        return <div className="text-red-500">Activity not found</div>
    }

    // Only typing practice needs group selection
    const needsGroupSelection = launchData.activity.activity_type === 'typing';

    // For activities that don't need group selection
    if (!needsGroupSelection) {
        return (
            <div className="max-w-2xl mx-auto space-y-6">
                <h1 className="text-2xl font-bold">
                    {launchData.activity.title}
                </h1>
                <Button 
                    onClick={handleDirectLaunch}
                    className="w-full"
                >
                    Launch Now
                </Button>
            </div>
        )
    }

    // For typing and writing activities, show group selection
    return (
        <div className="max-w-2xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold">
                {launchData.activity.title}
            </h1>
            
            <div className="space-y-4">
                <div className="space-y-2">
                    <label className="text-sm font-medium">
                        Select Word Group
                    </label>
                    <Select 
                        onValueChange={setSelectedGroup} 
                        value={selectedGroup}
                    >
                        <SelectTrigger>
                            <SelectValue 
                                placeholder="Select a word group" 
                            />
                        </SelectTrigger>
                        <SelectContent>
                            {launchData.groups?.map((group) => (
                                <SelectItem 
                                    key={group.id} 
                                    value={group.id.toString()}
                                >
                                    {group.name}
                                </SelectItem>
                            ))}
                        </SelectContent>
                    </Select>
                </div>

                <Button 
                    onClick={launchData.activity.activity_type === 'typing' 
                        ? handleTypingLaunch 
                        : handleDirectLaunch}
                    disabled={!selectedGroup}
                    className="w-full"
                >
                    Launch Now
                </Button>
            </div>
        </div>
    )
}
