"""
TrendPulse - Sample Dataset Generator
Generates a realistic YouTube trending dataset for testing/demo.
"""
import csv, json, random, hashlib
from datetime import datetime, timedelta
from pathlib import Path

random.seed(42)

CATEGORIES = {
    1:"Film & Animation",2:"Autos & Vehicles",10:"Music",15:"Pets & Animals",
    17:"Sports",19:"Travel & Events",20:"Gaming",22:"People & Blogs",23:"Comedy",
    24:"Entertainment",25:"News & Politics",26:"Howto & Style",
    27:"Education",28:"Science & Technology",29:"Nonprofits & Activism"
}
CHANNELS = ["TechInsider","ViralNow","ComedyGold","MusicVibes","SportsCentral",
            "GamingPro","LifestyleHub","NewsDesk","ScienceExplained","EntertainmentWeekly",
            "FoodLover","TravelWorld","PetVideos","EducationFirst","HealthTips"]
TITLE_TEMPLATES = [
    "The INCREDIBLE Story of {topic} That Nobody Talks About",
    "{topic}: Everything You Need to Know in 2024",
    "Why {topic} Is Changing Everything",
    "I Tried {topic} For 30 Days - Here Are The Results",
    "{topic} Explained In Under 10 Minutes",
    "SHOCKING: {topic} Revealed!",
    "Top 10 {topic} Facts That Will Blow Your Mind",
    "How {topic} Works - A Complete Guide",
    "{topic} vs {topic2}: The Ultimate Comparison",
    "LIVE: {topic} Breaking News Update",
]
TOPICS = ["AI","Bitcoin","Climate Change","Space Travel","Social Media","Gaming",
          "Music Industry","Electric Cars","Remote Work","Cryptocurrency",
          "Streaming Wars","Diet Culture","Mental Health","Fitness","Cooking",
          "Fashion","Travel","Education","Politics","Technology"]


def make_video_id(n: int) -> str:
    return hashlib.md5(str(n).encode()).hexdigest()[:11]

def generate_title(idx: int) -> str:
    t = random.choice(TITLE_TEMPLATES)
    tp = random.choice(TOPICS)
    tp2 = random.choice([x for x in TOPICS if x != tp])
    return t.format(topic=tp, topic2=tp2)

def generate_sample_dataset(num_videos: int = 500,
                            output_path: str = "data/sample/sample_youtube_trending.csv"):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    base_date = datetime(2023, 1, 1)
    rows = []
    for i in range(num_videos):
        vid_id = make_video_id(i)
        category_id = random.choice(list(CATEGORIES.keys()))
        channel = random.choice(CHANNELS)
        title = generate_title(i)
        views = random.randint(50000, 15000000)
        likes = int(views * random.uniform(0.01, 0.12))
        dislikes = int(likes * random.uniform(0.01, 0.15))
        comments = int(views * random.uniform(0.001, 0.05))
        pub_offset = timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))
        publish_time = base_date + pub_offset
        num_trending = random.choices(range(1, 16),
            weights=[20,18,15,12,10,8,5,4,3,2,1,1,1,0.5,0.5], k=1)[0]
        for j in range(num_trending):
            td = publish_time + timedelta(days=random.randint(1,7) + j)
            rows.append({
                "video_id": vid_id,
                "trending_date": td.strftime("%y.%d.%m"),
                "title": title,
                "channel_title": channel,
                "category_id": category_id,
                "publish_time": publish_time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "tags": "|".join(random.sample(TOPICS, k=random.randint(1,8))),
                "views": views + random.randint(0, 100000),
                "likes": likes,
                "dislikes": dislikes,
                "comment_count": comments,
                "thumbnail_link": f"https://img.youtube.com/vi/{vid_id}/default.jpg",
                "comments_disabled": random.choice(["False"]*9+["True"]),
                "ratings_disabled": random.choice(["False"]*19+["True"]),
                "video_error_or_removed": "False",
                "description": f"Video about {title[:40]}. " * random.randint(1,5)
            })
    random.shuffle(rows)
    fieldnames = ["video_id","trending_date","title","channel_title","category_id",
                  "publish_time","tags","views","likes","dislikes","comment_count",
                  "thumbnail_link","comments_disabled","ratings_disabled",
                  "video_error_or_removed","description"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated {len(rows)} observations for {num_videos} videos -> {output_path}")
    cat_json = {"kind":"youtube#videoCategoryListResponse","etag":"sample","items":[
        {"id":str(k),"kind":"youtube#videoCategory","snippet":{"title":v,"assignable":True}}
        for k,v in CATEGORIES.items()]}
    cat_path = Path(output_path).parent / "US_category_id.json"
    with open(cat_path, "w") as f:
        json.dump(cat_json, f, indent=2)
    print(f"Generated category JSON -> {cat_path}")
    return output_path

if __name__ == "__main__":
    generate_sample_dataset(num_videos=500)
