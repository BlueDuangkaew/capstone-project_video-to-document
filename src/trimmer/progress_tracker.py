class ProgressTracker:
    def __init__(self, total_segments):
        self.total = total_segments
        self.completed = 0

    def update(self):
        self.completed += 1

    def status(self):
        return {
            "completed": self.completed,
            "total": self.total,
            "percent": round((self.completed / self.total) * 100, 2)
        }

    def __str__(self):
        return f"{self.completed}/{self.total} segments processed ({self.status()['percent']}%)"
