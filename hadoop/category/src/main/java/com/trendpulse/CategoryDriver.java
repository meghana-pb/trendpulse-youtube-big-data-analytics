package com.trendpulse;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;

/**
 * TrendPulse - Category Analysis MapReduce Driver
 * Usage: CategoryDriver <input_path> <output_path>
 */
public class CategoryDriver {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: CategoryDriver <input> <output>");
            System.exit(1);
        }
        Configuration conf = new Configuration();
        Job job = Job.getInstance(conf, "TrendPulse-CategoryAnalysis");
        job.setJarByClass(CategoryDriver.class);
        job.setMapperClass(CategoryMapper.class);
        job.setReducerClass(CategoryReducer.class);
        job.setOutputKeyClass(Text.class);
        job.setOutputValueClass(Text.class);
        job.setNumReduceTasks(1);
        FileInputFormat.addInputPath(job, new Path(args[0]));
        FileOutputFormat.setOutputPath(job, new Path(args[1]));
        System.out.println("[TrendPulse] Category Analysis job submitted.");
        System.exit(job.waitForCompletion(true) ? 0 : 1);
    }
}
