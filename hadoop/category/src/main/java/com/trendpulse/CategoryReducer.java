package com.trendpulse;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
import java.io.IOException;

/**
 * TrendPulse - Category Analysis Reducer
 * Output: category_id TAB count|avg_views|avg_likes|avg_comments|avg_engagement|avg_trending|max_trending|min_trending
 */
public class CategoryReducer extends Reducer<Text, Text, Text, Text> {

    @Override
    public void reduce(Text key, Iterable<Text> values, Context context)
            throws IOException, InterruptedException {
        long count = 0;
        long totalViews = 0, totalLikes = 0, totalComments = 0;
        double totalEngagement = 0.0, totalTrending = 0.0;
        int maxTrending = 0, minTrending = Integer.MAX_VALUE;

        for (Text val : values) {
            String[] parts = val.toString().split("\\|");
            if (parts.length < 5) continue;
            try {
                long views = Long.parseLong(parts[0]);
                long likes = Long.parseLong(parts[1]);
                long comments = Long.parseLong(parts[2]);
                double engRate = Double.parseDouble(parts[3]);
                int trending = Integer.parseInt(parts[4]);

                totalViews += views;
                totalLikes += likes;
                totalComments += comments;
                totalEngagement += engRate;
                totalTrending += trending;
                if (trending > maxTrending) maxTrending = trending;
                if (trending < minTrending) minTrending = trending;
                count++;
            } catch (NumberFormatException e) {
                // skip malformed
            }
        }

        if (count == 0) return;
        if (minTrending == Integer.MAX_VALUE) minTrending = 1;

        double avgViews = (double) totalViews / count;
        double avgLikes = (double) totalLikes / count;
        double avgComments = (double) totalComments / count;
        double avgEngagement = totalEngagement / count;
        double avgTrending = totalTrending / count;

        String result = String.format("%d|%.2f|%.2f|%.2f|%.6f|%.2f|%d|%d",
                count, avgViews, avgLikes, avgComments, avgEngagement, avgTrending, maxTrending, minTrending);
        context.write(key, new Text(result));
    }
}
