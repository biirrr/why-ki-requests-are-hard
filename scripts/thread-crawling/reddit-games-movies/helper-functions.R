require("tidyverse")
require("glue")
require("here")


event_log_filename <- "log.events.txt"


# Function for reading in the list of subreddits to be crawled.
get_subreddit_list <- function(list_filename) {

  # Read in the list of subreddits to be crawled.
  subreddit_list <- read_csv(list_filename, col_names = c("subreddit"), show_col_types = FALSE) %>% 
    # Remove all commented lines (= these represent subreddits that should not be crawled).
    filter(!str_detect(subreddit, "#")) %>% 
    # Remove any leading '/r/' strings.
    mutate(subreddit = str_replace(subreddit, "/r/", "")) %>% 
    # Turn it into a vector.
    pull()

  # Return the list.
  subreddit_list
  
}



# Function for reading in the crawling log.
get_crawling_log <- function(log_filename, subreddit_list) {
  
  # Make sure the crawling log exists and is read in.
  if (file.exists(log_filename)) {
    
    # Read in the crawling log data on which subreddits have already been crawled.
    crawling_log <- read_tsv(log_filename, show_col_types = FALSE, 
                             col_names = TRUE, col_types = "ccTnc")
    
    # Remove the part of the crawling log that is not supposed to be crawled.
    # Only active threads should be crawled.
    crawling_log <- filter(crawling_log, (subreddit %in% subreddit_list))
    
    # # Only subreddits active in the subreddit list should be crawled.
    # crawling_log <- filter(crawling_log, status == "active")
    
    # If the file doesn't exist yet, create an empty one.
  } else {
    
    # Create an empty tibble with the right columns.
    crawling_log <- tibble(subreddit = character(), thread_id = character(), 
                           crawling_timestamp = as_datetime(0), comments = numeric(),
                           status = character())
    
    # Save this empty tibble.
    crawling_log %>% write_tsv(log_filename)
    
  }
  
  # Return the crawling log.
  return(crawling_log)

}



# Function for determining which object to crawl---comments or threads---based on which
# half of the hour we are in.
pick_object_to_crawl <- function() {
  
  # Define options.
  CRAWL_THREADS <- 1
  CRAWL_COMMENTS <- 2
  
  # First half of the hour? Then crawl threads.
  minute = minute(now())
  if (minute <= 30) {
    return(CRAWL_THREADS)
  # Second half of the hour? Then crawl comments.
  } else {
    return(CRAWL_COMMENTS)
  }

}



# Function for logging events in the log file with the current timestamp.
log_event <- function(event_description, message = FALSE) {
  log_message <- glue("{substr(as.character(now()), 1, 19)}   {event_description}")
  if (message == TRUE) {
    # message(log_message)
    print(log_message)
  }
  write_lines(log_message, event_log_filename, append=TRUE)
}



# Function for initializing the name of the event log.
set_event_log_name <- function(createevent_log_filename) {
  event_log_filename <- event_log_filename
}



# Function for reading in all the threads previously crawled for a subreddit.
get_subreddit_crawl <- function(thread_crawl_dir, subreddit) {
  
  # Check whether the directory exists already. If not, create it.
  if (!file.exists(thread_crawl_dir)) {
    dir.create(file.path(thread_crawl_dir))
  } 
  
  # Check whether the crawled threads file exists already. If it does, read it in.
  thread_crawl_filename <- glue("{thread_crawl_dir}/threads.{subreddit}.tsv")
  if (file.exists(thread_crawl_filename)) {
    
    # Read in the file.
    old_threads <- read_tsv(thread_crawl_filename, show_col_types = FALSE) %>% distinct()
    
  # If not, create an empty tibble instead.
  } else {
    
    # Create an empty tibble.
    old_threads <- tibble(thread_id = character(), timestamp = as_datetime(0), 
                          subreddit = character(), title = character(),
                          text = character(), comments = numeric(), url = character())
    
  }
  
  # Return the tibble.
  return(old_threads)

}
  


# Function for cleaning the text in posts and comments.
clean_text <- function(text) {
  
  # Replace all non-space whitespaces with spaces.
  text_cleaned <- str_replace_all(text, "[:space:]+", " ")
  
  # Remove the double quotes that for some reason keep getting inserted.
  text_cleaned <- str_replace_all(text_cleaned, "[\"]+", "\"")
  text_cleaned = str_squish(text_cleaned)
  return(text_cleaned)
  
}



# Function for saving a tibble with crawled comments to file.
save_thread_comments <- function(all_comments, thread_crawl_dir, current_thread_id, prefix_length = 3) {

  # Check whether the directory exists already. If not, create it.
  if (!file.exists(thread_crawl_dir)) {
    dir.create(file.path(thread_crawl_dir))
  }
  
  # Check whether the subdir exists already. If not, create it.
  subdir <- str_sub(current_thread_id, 1, prefix_length)
  subdir_path <- glue("{thread_crawl_dir}/{subdir}")
  if (!file.exists(subdir_path)) {
    dir.create(file.path(subdir_path))
  }
  
  # Write to file.
  comment_file_path <- glue("{subdir_path}/comments.{current_thread_id}.tsv")
  write_tsv(all_comments, comment_file_path)
  
}



# Function for reading in all the comments previously crawled for a subreddit 
# thread.
get_thread_comments <- function(thread_crawl_dir, thread_id, prefix_length = 3) {
  
  # Check whether the directory exists already. If not, create it.
  if (!file.exists(thread_crawl_dir)) {
    dir.create(file.path(thread_crawl_dir))
  }
  
  # Check whether the crawled comments file exists already. If it does, read it in.
  subdir <- str_sub(thread_id, 1, prefix_length)
  comments_crawl_filename <- glue("{thread_crawl_dir}/{subdir}/comments.{thread_id}.tsv")
  if (file.exists(comments_crawl_filename)) {
    
    # Read in the file.
    old_comments <- read_tsv(comments_crawl_filename, show_col_types = FALSE, col_types = "ccccTcdddd")
    
    # If not, create an empty tibble instead.
  } else {
    
    # Create an empty tibble.
    old_comments <- tibble(subreddit = character(), thread_id = character(), 
                           comment_id = character(), author = character(), 
                           timestamp = as_datetime(0), comment = character(), 
                           score = numeric(), upvotes = numeric(), 
                           downvotes = numeric(), golds = numeric())
    
  }
  
  # Return the tibble.
  return(old_comments)
  
}


# Helper functions for properly formatting/rounding numbers.
round0 <- function(number) {
  return(scales::label_comma(accuracy = NULL)(number))
}
round1 <- function(number) {
  return(scales::label_comma(accuracy = 0.1)(number))
}
round2 <- function(number) {
  return(scales::label_comma(accuracy = 0.01)(number))
}
round3 <- function(number) {
  return(scales::label_comma(accuracy = 0.001)(number))
}



# Function for getting the number of crawled comments for a thread.
get_crawled_comment_count <- function(subreddits_dir, subreddit, thread_id) {
  
  # Specify the path to the crawled comments file.
  comment_crawl_path <- glue("{subreddits_dir}/{subreddit}/comments.{thread_id}.tsv")
  
  # Check whether it exist. If it does, read the file and count the number of rows.
  # If not, return NA.
  if (file.exists(comment_crawl_path)) {
    comment_count <- read_tsv(comment_crawl_path, show_col_types = FALSE) %>% nrow()
    return(comment_count - 1)  # First comment is the original post
  } else {
    return(NA)
  }
  
}


# This function goes through a tibble of threads and removes duplicates. More
# specifically, it makes sure that the thread instance with the longest (and
# therefore most updated) request text ('text') is kept.
remove_thread_duplicates <- function(threads_tibble) {
  
  deduplicated_tibble <- threads_tibble %>% 
    
    # For each thread ID, find the one with the longest text length. Remove
    # the other one.
    group_by(thread_id) %>%
    mutate(max_text_length = max(str_length(text))) %>%
    filter(max_text_length == str_length(text)) %>%
    # Do some clean-up.
    ungroup() %>% 
    select(-max_text_length)
  
  # Return the deduplicated version.
  return(deduplicated_tibble)
  
} 


# This function calculates the right date at which a comment was posted based
# on the crawling date and a differential time string, such as "a day ago" or
# "4 months ago".
calculate_comment_date <- function(crawl_timestamp, subtraction_string) {
  
  # Extract the unit duration and convert to a double. In case the unit duration
  # was a string (e.g., "one" in "one year ago") convert this to a number.
  unit_duration <- str_split(subtraction_string, " ")[[1]][1]
  if (unit_duration == "one" | unit_duration == "a" | unit_duration == "an") {
    unit_duration <- 1
  } 
  unit_duration <- as.double(unit_duration)
  
  # Extract the unit of time.
  unit_of_time <- str_split(subtraction_string, " ")[[1]][2]
  if (unit_of_time == "hour") {
    unit_of_time = "hours"
  }
  if (unit_of_time == "day") {
    unit_of_time = "days"
  }
  if (unit_of_time == "month") {
    unit_of_time = "months"
  }
  if (unit_of_time == "year") {
    unit_of_time = "years"
  }
  
  # Add the specified duration to the first timestamp.
  updated_timestamp <- NA
  if (unit_of_time == "hours") {
    updated_timestamp <- crawl_timestamp
  }
  if (unit_of_time == "days") {
    updated_timestamp <- crawl_timestamp - lubridate::days(unit_duration)
  }
  if (unit_of_time == "months") {
    updated_timestamp <- crawl_timestamp %m-% months(unit_duration)
  }
  if (unit_of_time == "years") {
    updated_timestamp <- crawl_timestamp - lubridate::years(unit_duration)
  }
  
  # Return the new date.
  return(updated_timestamp)
  
}