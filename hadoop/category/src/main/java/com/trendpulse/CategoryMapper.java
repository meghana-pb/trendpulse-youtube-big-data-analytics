package com.trendpulse;

import org.apache.hadoop.io.LongWritable;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import java.io.IOException;

/**
 * TrendPulse - Category Analysis Mapper
 * Emits: (category_id, views|likes|comments|engagement_rate|trending_duration)
 */
public class CategoryMapper extends Mapper<LongWritable, Text, Text, Text> {

    private static final int IDX_VIDEO_ID = 0;
    private static final int IDX_CATEGORY_ID = 3;
    private static final int IDX_VIEWS = 8;
    private static final int IDX_LIKES = 9;
    private static final int IDX_COMMENTS = 11;
    private static final int IDX_ENGAGEMENT_RATE = 17;
    private static final int IDX_TRENDING_DURATION = 27;

    private boolean isHeader = true;

    @Override
    public void map(LongWritable key, Text value, Context context)
            throws IOException, InterruptedException {
        String line = value.toString().trim();
        if (isHeader && line.startsWith("video_id")) {
            isHeader = false;
            return;
        }
        isHeader = false;
        if (line.isEmpty()) return;

        String[] cols = parseCsvLine(line);
        if (cols.length < 20) return;

        try {
            String categoryId = cols[IDX_CATEGORY_ID].trim();
            if (categoryId.isEmpty() || categoryId.equals("0")) return;

            long views = parseLong(cols, IDX_VIEWS);
            long likes = parseLong(cols, IDX_LIKES);
            long comments = parseLong(cols, IDX_COMMENTS);
            double engRate = parseDouble(cols, IDX_ENGAGEMENT_RATE);
            int trendDuration = parseInt(cols, IDX_TRENDING_DURATION, 1);

            String output = views + "|" + likes + "|" + comments + "|" + engRate + "|" + trendDuration;
            context.write(new Text(categoryId), new Text(output));
        } catch (Exception e) {
            context.getCounter("TrendPulse", "MalformedRecords").increment(1);
        }
    }

    private long parseLong(String[] cols, int idx) {
        if (idx >= cols.length) return 0;
        try { return Math.max(0, Long.parseLong(cols[idx].trim().replace("\"", ""))); }
        catch (NumberFormatException e) { return 0; }
    }

    private double parseDouble(String[] cols, int idx) {
        if (idx >= cols.length) return 0.0;
        try { return Double.parseDouble(cols[idx].trim().replace("\"", "")); }
        catch (NumberFormatException e) { return 0.0; }
    }

    private int parseInt(String[] cols, int idx, int defaultVal) {
        if (idx >= cols.length) return defaultVal;
        try { return Math.max(1, Integer.parseInt(cols[idx].trim().replace("\"", ""))); }
        catch (NumberFormatException e) { return defaultVal; }
    }

    private String[] parseCsvLine(String line) {
        java.util.List<String> fields = new java.util.ArrayList<>();
        StringBuilder sb = new StringBuilder();
        boolean inQuotes = false;
        for (char c : line.toCharArray()) {
            if (c == '"') { inQuotes = !inQuotes; }
            else if (c == ',' && !inQuotes) { fields.add(sb.toString()); sb = new StringBuilder(); }
            else { sb.append(c); }
        }
        fields.add(sb.toString());
        return fields.toArray(new String[0]);
    }
}
