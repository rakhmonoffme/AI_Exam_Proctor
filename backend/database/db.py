from pymongo import MongoClient
from gridfs import GridFS
from datetime import datetime
import os

class ProctoringDatabase:
    def __init__(self, mongo_uri='mongodb://localhost:27017/', db_name='proctoring_db'):
        """
        Initialize MongoDB connection for proctoring system
        
        Args:
            mongo_uri: MongoDB connection string
            db_name: Database name
        """
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.fs = GridFS(self.db)
        
        # Collections
        self.flagged_intervals = self.db['flagged_intervals']
        self.sessions = self.db['sessions']
        self.violations = self.db['violations']
        
        print(f"✓ Connected to MongoDB: {db_name}")
    
    def save_flagged_interval(self, flag_data, video_file_path, folder_path='flagged_videos'):
        """
        Save flagged interval with video organized by user
        
        Args:
            flag_data: Dictionary with interval information
            video_file_path: Path to video file
            folder_path: Base folder to save videos
            
        Returns:
            Inserted document ID
        """
        try:
            # Create user folder: flagged_videos/user_123/
            user_id = flag_data.get('user_id', flag_data.get('session_id', 'unknown_user'))
            
            user_folder = os.path.join(folder_path, user_id)
            os.makedirs(user_folder, exist_ok=True)
            
            # Generate permanent filename with timestamp and score
            timestamp = flag_data['interval_start'].replace(':', '-').replace('.', '-')
            permanent_filename = f"flagged_{timestamp}_score{flag_data['score']}.mp4"
            permanent_path = os.path.join(user_folder, permanent_filename)
            
            # Move video to permanent location
            if os.path.exists(video_file_path):
                os.rename(video_file_path, permanent_path)
                print(f"✓ Video saved to: {permanent_path}")
            
            # Add video reference
            flag_data['video_path'] = permanent_path
            flag_data['video_filename'] = permanent_filename
            flag_data['saved_at'] = datetime.now().isoformat()
            
            # Insert into collection
            result = self.flagged_intervals.insert_one(flag_data)
            
            print(f"✓ Flagged interval saved to MongoDB (ID: {result.inserted_id})")
            
            return result.inserted_id
            
        except Exception as e:
            print(f"✗ Error saving: {e}")
            return None
    
    def get_video(self, video_id):
        """
        Retrieve video from GridFS
        
        Args:
            video_id: GridFS video ID
            
        Returns:
            Video data as bytes
        """
        try:
            video_file = self.fs.get(video_id)
            return video_file.read()
        except Exception as e:
            print(f"✗ Error retrieving video: {e}")
            return None
    
    def save_video_to_file(self, video_id, output_path):
        """
        Save video from GridFS to file
        
        Args:
            video_id: GridFS video ID
            output_path: Output file path
            
        Returns:
            True if successful
        """
        try:
            video_data = self.get_video(video_id)
            if video_data:
                with open(output_path, 'wb') as f:
                    f.write(video_data)
                print(f"✓ Video saved to {output_path}")
                return True
            return False
        except Exception as e:
            print(f"✗ Error saving video to file: {e}")
            return False
    
    def get_all_flagged_intervals(self, limit=None, sort_by='flagged_at', ascending=False):
        """
        Get all flagged intervals
        
        Args:
            limit: Maximum number of results
            sort_by: Field to sort by
            ascending: Sort order
            
        Returns:
            List of flagged intervals
        """
        try:
            query = self.flagged_intervals.find()
            
            # Sort
            sort_order = 1 if ascending else -1
            query = query.sort(sort_by, sort_order)
            
            # Limit
            if limit:
                query = query.limit(limit)
            
            return list(query)
        except Exception as e:
            print(f"✗ Error retrieving flagged intervals: {e}")
            return []
    
    def get_flagged_interval_by_id(self, interval_id):
        """
        Get specific flagged interval by ID
        
        Args:
            interval_id: Document ID
            
        Returns:
            Flagged interval document
        """
        try:
            from bson.objectid import ObjectId
            return self.flagged_intervals.find_one({'_id': ObjectId(interval_id)})
        except Exception as e:
            print(f"✗ Error retrieving interval: {e}")
            return None
    
    def get_intervals_by_score(self, min_score=10, max_score=None):
        """
        Get flagged intervals filtered by score
        
        Args:
            min_score: Minimum score
            max_score: Maximum score (optional)
            
        Returns:
            List of flagged intervals
        """
        try:
            query = {'score': {'$gte': min_score}}
            if max_score:
                query['score']['$lte'] = max_score
            
            return list(self.flagged_intervals.find(query))
        except Exception as e:
            print(f"✗ Error retrieving intervals by score: {e}")
            return []
    
    def get_intervals_by_violation_type(self, violation_type):
        """
        Get intervals that contain specific violation type
        
        Args:
            violation_type: Type of violation (e.g., 'multiple_faces')
            
        Returns:
            List of flagged intervals
        """
        try:
            query = {'violations.type': violation_type}
            return list(self.flagged_intervals.find(query))
        except Exception as e:
            print(f"✗ Error retrieving intervals by violation: {e}")
            return []
    
    def create_session(self, session_data):
        """
        Create a new monitoring session
        
        Args:
            session_data: Dictionary with session information
            
        Returns:
            Session ID
        """
        try:
            session_data['created_at'] = datetime.now().isoformat()
            session_data['status'] = 'active'
            result = self.sessions.insert_one(session_data)
            print(f"✓ Session created (ID: {result.inserted_id})")
            return result.inserted_id
        except Exception as e:
            print(f"✗ Error creating session: {e}")
            return None
    
    def update_session(self, session_id, update_data):
        """
        Update existing session
        
        Args:
            session_id: Session document ID
            update_data: Data to update
            
        Returns:
            True if successful
        """
        try:
            from bson.objectid import ObjectId
            update_data['updated_at'] = datetime.now().isoformat()
            result = self.sessions.update_one(
                {'_id': ObjectId(session_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"✗ Error updating session: {e}")
            return False
    
    def end_session(self, session_id, final_report):
        """
        Mark session as completed and save final report
        
        Args:
            session_id: Session document ID
            final_report: Final monitoring report
            
        Returns:
            True if successful
        """
        try:
            from bson.objectid import ObjectId
            update_data = {
                'status': 'completed',
                'ended_at': datetime.now().isoformat(),
                'final_report': final_report
            }
            result = self.sessions.update_one(
                {'_id': ObjectId(session_id)},
                {'$set': update_data}
            )
            print(f"✓ Session ended (ID: {session_id})")
            return result.modified_count > 0
        except Exception as e:
            print(f"✗ Error ending session: {e}")
            return False
    
    def get_session_statistics(self, session_id):
        """
        Get statistics for a session
        
        Args:
            session_id: Session document ID
            
        Returns:
            Statistics dictionary
        """
        try:
            from bson.objectid import ObjectId
            
            # Get session
            session = self.sessions.find_one({'_id': ObjectId(session_id)})
            if not session:
                return None
            
            # Get all flagged intervals for this session
            flagged = list(self.flagged_intervals.find({'session_id': str(session_id)}))
            
            stats = {
                'session_id': str(session_id),
                'total_flags': len(flagged),
                'total_violations': sum(len(f.get('violations', [])) for f in flagged),
                'average_score': sum(f.get('score', 0) for f in flagged) / len(flagged) if flagged else 0,
                'max_score': max((f.get('score', 0) for f in flagged), default=0),
                'session_status': session.get('status', 'unknown')
            }
            
            return stats
            
        except Exception as e:
            print(f"✗ Error getting session statistics: {e}")
            return None
    
    def delete_video(self, video_id):
        """
        Delete video from GridFS
        
        Args:
            video_id: GridFS video ID
            
        Returns:
            True if successful
        """
        try:
            self.fs.delete(video_id)
            print(f"✓ Video deleted (ID: {video_id})")
            return True
        except Exception as e:
            print(f"✗ Error deleting video: {e}")
            return False
    
    def cleanup_old_data(self, days=30):
        """
        Delete data older than specified days
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of deleted records
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Find old intervals
            old_intervals = self.flagged_intervals.find({
                'saved_at': {'$lt': cutoff_date.isoformat()}
            })
            
            deleted_count = 0
            for interval in old_intervals:
                # Delete video
                if 'video_id' in interval:
                    self.fs.delete(interval['video_id'])
                
                # Delete interval record
                self.flagged_intervals.delete_one({'_id': interval['_id']})
                deleted_count += 1
            
            print(f"✓ Cleaned up {deleted_count} old records")
            return deleted_count
            
        except Exception as e:
            print(f"✗ Error cleaning up data: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection"""
        self.client.close()
        print("✓ MongoDB connection closed")


# Example usage
if __name__ == "__main__":
    # Initialize database
    db = ProctoringDatabase()
    
    # Create a test session
    session_data = {
        'user_id': 'user123',
        'exam_id': 'exam456',
        'start_time': datetime.now().isoformat()
    }
    session_id = db.create_session(session_data)
    
    # Get all flagged intervals
    flagged = db.get_all_flagged_intervals(limit=10)
    print(f"\nTotal flagged intervals: {len(flagged)}")
    
    # Get session statistics
    if session_id:
        stats = db.get_session_statistics(session_id)
        print(f"\nSession Stats: {stats}")
    
    # Close connection
    db.close()