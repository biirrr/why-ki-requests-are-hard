# Import relevant packages.
require("glue")                # Easier string formatting
library("here")                # Easy shortcut for the root RStudio project dir
library("tidyverse")           # All useful tidyverse packages
library("fs")                  # Handling file operations
library("crayon")              # Colored text in the R console messages
library("jsonlite")
library("car")
library("nlme")
library("skimr")
library("reshape")
library("broom")



# Define the relevant directories.
base_dir <- here()
merged_data_dir <- glue("{base_dir}/data/merged")  # Update this to the directory that contains the JSON files


# Read in the helper functions.
source(glue("{base_dir}/helper-functions.R"))



### ETL ########################################################################

## GAMES
# Read in the merged JSON data from Mark.
games_filename <- glue("{merged_data_dir}/games.json")
data_json_object <- fromJSON(games_filename)

# Get the thread IDs.
thread_id_list <- data_json_object$data$thread_id
tibble_thread_ids <- as_tibble(thread_id_list) %>% 
  dplyr::rename(thread_id = value) %>% 
  mutate(thread_id = as.character(thread_id))

# Get the thread status.
category_list <- data_json_object$data$category
tibble_thread_categories <- as_tibble(category_list) %>% 
  dplyr::rename(status = value)

# Get the merged statistics.
stats_object <- data_json_object$stats
tibble_raw_stats <- dplyr::as_tibble(jsonlite::flatten(stats_object))

# Add the thread IDs.
tibble_all_stats_games <- dplyr::bind_cols(tibble_thread_ids, tibble_thread_categories, tibble_raw_stats) %>% 
  dplyr::rename(thread_popularity = score,
                item_popularity = popularity_score) %>% 
  # Convert first_publish_year to the number of years old the book is.
  mutate(item_age = ifelse(!is.na(first_publish_year), 2025 - first_publish_year, NA)) %>% 
  # Convert has_plot to binary numerical variable.
  mutate(has_plot = ifelse(has_plot, 1, 0)) %>% 
  # Remove columns we won't use for logistic regression.
  select(-title_length_chars, -text_length_chars, -full_post_length_chars,
         -replies_until_solved, -replies_until_confirmed, -OP_reply_count_before_confirmed,
         -solved_by_OP, -first_publish_year, -plot_character_length)


## BOOKS
# Read in the merged JSON data from Mark.
books_filename <- glue("{merged_data_dir}/books.json")
data_json_object <- fromJSON(books_filename)

# Get the thread IDs.
thread_id_list <- data_json_object$data$thread_id
tibble_thread_ids <- as_tibble(thread_id_list) %>% 
  dplyr::rename(thread_id = value) %>% 
  mutate(thread_id = as.character(thread_id))

# Get the thread status.
category_list <- data_json_object$data$category
tibble_thread_categories <- as_tibble(category_list) %>% 
  dplyr::rename(status = value)

# Get the merged statistics.
stats_object <- data_json_object$stats
tibble_raw_stats <- dplyr::as_tibble(jsonlite::flatten(stats_object))

# Add the thread IDs.
tibble_all_stats_books <- dplyr::bind_cols(tibble_thread_ids, tibble_thread_categories, tibble_raw_stats) %>% 
  dplyr::rename(thread_popularity = score,
                item_popularity = readinglog_count) %>% 
  # Convert first_publish_year to the number of years old the book is.
  mutate(item_age = ifelse(!is.na(first_publish_year), 2025 - first_publish_year, NA)) %>% 
  # Convert has_plot to binary numerical variable.
  mutate(has_plot = ifelse(has_plot, 1, 0)) %>% 
  # Remove columns we won't use for logistic regression.
  select(-title_length_chars, -text_length_chars, -full_post_length_chars,
         -replies_until_solved, -replies_until_confirmed, -OP_reply_count_before_confirmed,
         -solved_by_OP, -first_publish_year, -plot_character_length)


## MOVIES
# Read in the merged JSON data from Mark.
movies_filename <- glue("{merged_data_dir}/movies.json")
data_json_object <- fromJSON(movies_filename)

# Get the thread IDs.
thread_id_list <- data_json_object$data$thread_id
tibble_thread_ids <- as_tibble(thread_id_list) %>% 
  dplyr::rename(thread_id = value) %>% 
  mutate(thread_id = as.character(thread_id))

# Get the thread status.
category_list <- data_json_object$data$category
tibble_thread_categories <- as_tibble(category_list) %>% 
  dplyr::rename(status = value)

# Get the merged statistics.
stats_object <- data_json_object$stats
tibble_raw_stats <- dplyr::as_tibble(jsonlite::flatten(stats_object))

# Add the thread IDs.
tibble_all_stats_movies <- dplyr::bind_cols(tibble_thread_ids, tibble_thread_categories, tibble_raw_stats) %>% 
  dplyr::rename(thread_popularity = score,
                item_popularity = popularity_score) %>% 
  # Convert first_publish_year to the number of years old the book is.
  mutate(item_age = ifelse(!is.na(first_publish_year), 2025 - first_publish_year, NA)) %>% 
  # Convert has_plot to binary numerical variable.
  mutate(has_plot = ifelse(has_plot, 1, 0)) %>% 
  # Remove columns we won't use for logistic regression.
  select(-title_length_chars, -text_length_chars, -full_post_length_chars,
         -replies_until_solved, -replies_until_confirmed, -OP_reply_count_before_confirmed,
         -solved_by_OP, -first_publish_year, -plot_character_length)


## COMBINED
tibble_all_stats <- bind_rows(tibble_all_stats_books, tibble_all_stats_games, tibble_all_stats_movies)

# Now with domain as a variable.
tibble_all_stats_domain <- bind_rows(mutate(tibble_all_stats_books, domain = 1),
                                     mutate(tibble_all_stats_games, domain = 2),
                                     mutate(tibble_all_stats_movies, domain = 3)) %>% 
  relocate(domain, .after = "status")





### Logistic regression :: Solved vs. unsolved #################################

# Make subsets of the data for analysis.
tibble_solved_vs_unsolved <- tibble_all_stats %>% 
  mutate(outcome = ifelse(status == "solved" | status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)
tibble_solved_vs_unsolved_domain <- tibble_all_stats_domain %>% 
  mutate(outcome = ifelse(status == "solved" | status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)



# Remove the variables that don't make sense for unsolved vs. solved
#
# Variables with NA values:
#   48   unique_user_replies  CHECK THESE!
#   62   item_popularity      no unsolved threads have an answer item, so no item popularity either
#   62   genre_popularity     no unsolved threads have an answer item, so no genre popularity either
#   64   item_age             no unsolved threads have an answer item, so no item age either
final_solved_vs_unsolved <- tibble_solved_vs_unsolved %>% 
  select(-item_popularity, -genre_popularity, -item_age)
final_solved_vs_unsolved_domain <- tibble_solved_vs_unsolved_domain %>% 
  select(-item_popularity, -genre_popularity, -item_age)


# Order of promising variables:
#  * OP_reply_count             More feedback from OP helps solve requests
#  * full_post_length_words     Longer, more descriptive requests are better 
#  * thread_popularity          Thread that are more popular are more likely to be solved
# #  * unique_user_replies        More different users replying means more eyes and a better chance of being solved
#  * reply_counter              More replies means more activity and a better chance of being solved
#  * full_post_readability      More readable posts mean more people will read and therefore solve
#  * total_unique_labels        More unique aspects of the item described means greater chance of recognition by others
#  * total_labels               More aspects of the item described means greater chance of recognition by others
#  * has_plot                   Plot descriptions are longer so may match more users' memories
#  * plot_word_length           Longer plot descriptions provide more elements to match a user's memories
#  * title_length_words         Titles are the first thing people see, so more descriptive ones might make more users click on them
#  * unique_user_count          More users replying means a bigger chance of matching someone's memories (subsumed by replies)

# All variables + all domains.
logit_model_all <- glm(outcome ~ OP_reply_count + full_post_length_words + thread_popularity + reply_counter + 
                         full_post_readability + total_unique_labels + total_labels + has_plot + plot_word_length + 
                         title_length_words + unique_user_count, 
                       data = final_solved_vs_unsolved, na.action = na.exclude, family = "binomial")
summary(logit_model_all)
tidy(logit_model_all) %>% 
  mutate(exp_estimate = exp(estimate))
# performance::model_performance(logit_model_all)
performance::model_performance(logit_model_all) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()


# All significant variables + all domains.
logit_model_optimal <- glm(outcome ~ OP_reply_count + thread_popularity + reply_counter + 
                             full_post_readability + has_plot + unique_user_count,
                           data = final_solved_vs_unsolved, na.action = na.exclude, family = "binomial")
# summary(logit_model_optimal)
tidy(logit_model_optimal)
# performance::model_performance(logit_model_optimal)
# anova(logit_model_all, logit_model_optimal)
performance::model_performance(logit_model_optimal) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()
anova(logit_model_all, logit_model_optimal) %>% tidy() %>% filter(!is.na(df)) %>% mutate(output = ifelse(p.value < 0.001, "p < 0.001", glue("p = {round3(p.value)}"))) %>% select(output) %>% pull()
#
# Outcome: Lower/better BIC value, but not significant, so let's stick with the 
#          full model.


# Format as LaTeX table rows. This is regression coefficient table #1 in the paper.
bind_cols(
  tidy(logit_model_all) %>%
    mutate(exp_estimate = sprintf("%.3f", exp(estimate)),
           estimate = sprintf("%.3f", estimate),
           std.error = sprintf("%.3f", std.error),
           statistic = sprintf("%.3f", statistic),
           p.value = sprintf("%.3f", p.value)),
  confint(logit_model_all, level=0.95) %>% as_tibble() %>% dplyr::rename(low = `2.5 %`, high = `97.5 %`) %>% 
    mutate(confint = glue("[{sprintf('%.3f', low)}, {sprintf('%.3f', high)}]"))
) %>% 
  mutate(latex_string = glue("&   {estimate}  &   {exp_estimate}  & {std.error}  & {statistic} & {p.value}  & {confint} \\\\")) %>% 
  select(term, latex_string)


# All variables + all domains + domain as variable.
logit_model_all_domain <- glm(outcome ~ OP_reply_count + full_post_length_words + thread_popularity + reply_counter + 
                                full_post_readability + total_unique_labels + total_labels + has_plot + plot_word_length + 
                                title_length_words + unique_user_count + domain, 
                              data = final_solved_vs_unsolved_domain, na.action = na.exclude, family = "binomial")
summary(logit_model_all_domain)
tidy(logit_model_all_domain)
# performance::model_performance(logit_model_all)
performance::model_performance(logit_model_all_domain) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()
anova(logit_model_all, logit_model_all_domain) %>% tidy() %>% filter(!is.na(df)) %>% mutate(output = ifelse(p.value < 0.001, "p < 0.001", glue("p = {round3(p.value)}"))) %>% select(output) %>% pull()







### Logistic regression :: LLM-solved vs. LLM-unsolved ##########################

# Make subsets of the data for analysis.
tibble_human_vs_llm <- tibble_all_stats %>% 
  filter(status != "unsolved") %>%
  mutate(outcome = ifelse(status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)
tibble_human_vs_llm_domain <- tibble_all_stats_domain %>% 
  filter(status != "unsolved") %>%
  mutate(outcome = ifelse(status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)


# Remove the variables that don't make sense for LLM-solved vs. LLM-unsolved
#  * unique_user_count          
#  * unique_user_replies        
#  * OP_reply_count             
#  * thread_popularity          
#  * title_length_words         
#  * reply_counter              
final_human_vs_llm <- tibble_human_vs_llm %>% 
  select(-unique_user_count, -OP_reply_count, -thread_popularity, -title_length_words, -reply_counter)
final_human_vs_llm_domain <- tibble_human_vs_llm_domain %>% 
  select(-unique_user_count, -OP_reply_count, -thread_popularity, -title_length_words, -reply_counter)


# Order of promising variables:
#  * item_popularity            More popular items have more text written about and are more likely seen by the LLM
#  * genre_popularity           More popular genres have more text written about and are more likely seen by the LLM
#  * full_post_length_words     Longer, more descriptive requests are more likely to match to what the LLM has seen
#  * total_unique_labels        More unique aspects of the item described means greater chance of matching to what the LLM has seen
#  * total_labels               More aspects of the item described means greater chance to match what the LLM has seen
#  * has_plot                   Plot descriptions are longer so more opportunity to match text out there
#  * plot_word_length           Longer plot descriptions provide more elements to match to what the LLM has seen
#  * item_age                   Maybe a concave curve with older ones less mentioned and more recent not mentioned enough yet, but middle ones well-represented
#  * full_post_readability      More readable posts might be easier for the LLM?

# All variables.
logit_model_all_llm <- glm(outcome ~ item_popularity + genre_popularity + full_post_length_words + total_unique_labels + 
                         total_labels + has_plot + plot_word_length + item_age + full_post_readability, 
                       data = final_human_vs_llm, na.action = na.exclude, family = "binomial")
summary(logit_model_all_llm)
tidy(logit_model_all_llm)
# performance::model_performance(logit_model_all_llm)
performance::model_performance(logit_model_all_llm) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()


# All significant variables.
logit_model_optimal_llm <- glm(outcome ~ has_plot, 
                               data = final_human_vs_llm, na.action = na.exclude, family = "binomial")
summary(logit_model_optimal)
tidy(logit_model_optimal_llm)
# performance::model_performance(logit_model_optimal_llm)
# anova(logit_model_all_llm, logit_model_optimal_llm)
performance::model_performance(logit_model_optimal_llm) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()
anova(logit_model_all_llm, logit_model_optimal_llm) %>% tidy() %>% filter(!is.na(df)) %>% mutate(output = ifelse(p.value < 0.001, "p < 0.001", glue("p = {round3(p.value)}"))) %>% select(output) %>% pull()
#
# Outcome: Lower/better BIC value, but cannot compare the models due to different 
#          sample sizes (because of missing values), so let's stick with the full 
#          model.


# All variables.
logit_model_all_llm <- glm(outcome ~ item_popularity + genre_popularity + full_post_length_words + total_unique_labels + 
                             total_labels + has_plot + plot_word_length + item_age + full_post_readability, 
                           data = final_human_vs_llm, na.action = na.exclude, family = "binomial")
summary(logit_model_all_llm)
tidy(logit_model_all_llm)
# performance::model_performance(logit_model_all_llm)
performance::model_performance(logit_model_all_llm) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()


# Format as LaTeX table rows. This is regression coefficient table #2 in the paper.
bind_cols(
  tidy(logit_model_all_llm) %>%
    mutate(exp_estimate = sprintf("%.3f", exp(estimate)),
           estimate = sprintf("%.3f", estimate),
           std.error = sprintf("%.3f", std.error),
           statistic = sprintf("%.3f", statistic),
           p.value = sprintf("%.3f", p.value)),
  confint(logit_model_all_llm, level=0.95) %>% as_tibble() %>% dplyr::rename(low = `2.5 %`, high = `97.5 %`) %>% 
    mutate(confint = glue("[{sprintf('%.3f', low)}, {sprintf('%.3f', high)}]"))
) %>% 
  mutate(latex_string = glue("&   {estimate}  &   {exp_estimate}  & {std.error}  & {statistic} & {p.value}  & {confint} \\\\")) %>% 
  select(term, latex_string)


# All variables + all domains + domain as variable.
logit_model_all_llm_domain <- glm(outcome ~ item_popularity + genre_popularity + full_post_length_words + total_unique_labels + 
                                    total_labels + has_plot + plot_word_length + item_age + full_post_readability + domain, 
                              data = final_human_vs_llm_domain, na.action = na.exclude, family = "binomial")
summary(logit_model_all_llm_domain)
tidy(logit_model_all_domain)
# performance::model_performance(logit_model_all_llm_domain)
performance::model_performance(logit_model_all_llm_domain) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()
anova(logit_model_all_llm, logit_model_all_llm_domain) %>% tidy() %>% filter(!is.na(df)) %>% mutate(output = ifelse(p.value < 0.001, "p < 0.001", glue("p = {round3(p.value)}"))) %>% select(output) %>% pull()





### Logistic regression :: Solved vs. unsolved :: Separate domains #############

# Make subsets of the data for analysis.
tibble_solved_vs_unsolved_books <- tibble_all_stats_books %>% 
  mutate(outcome = ifelse(status == "solved" | status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)

# Remove the variables that don't make sense for unsolved vs. solved
final_solved_vs_unsolved_books <- tibble_solved_vs_unsolved_books %>% 
  select(-item_popularity, -genre_popularity, -item_age)

# All variables / Only books.
logit_model_all_books <- glm(outcome ~ OP_reply_count + full_post_length_words + thread_popularity + reply_counter + 
                         full_post_readability + total_unique_labels + total_labels + has_plot + plot_word_length + 
                         title_length_words + unique_user_count, 
                       data = final_solved_vs_unsolved_books, na.action = na.exclude, family = "binomial")
summary(logit_model_all_books)
tidy(logit_model_all_books)
# performance::model_performance(logit_model_all_books)
performance::model_performance(logit_model_all_books) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()


# Make subsets of the data for analysis.
tibble_solved_vs_unsolved_games <- tibble_all_stats_games %>% 
  mutate(outcome = ifelse(status == "solved" | status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)

# Remove the variables that don't make sense for unsolved vs. solved
final_solved_vs_unsolved_games <- tibble_solved_vs_unsolved_games %>% 
  select(-item_popularity, -genre_popularity, -item_age)

# All variables / Only games.
logit_model_all_games <- glm(outcome ~ OP_reply_count + full_post_length_words + thread_popularity + reply_counter + 
                               full_post_readability + total_unique_labels + total_labels + has_plot + plot_word_length + 
                               title_length_words + unique_user_count, 
                             data = final_solved_vs_unsolved_games, na.action = na.exclude, family = "binomial")
summary(logit_model_all_games)
tidy(logit_model_all_games)
# performance::model_performance(logit_model_all_games)
performance::model_performance(logit_model_all_games) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()



# Make subsets of the data for analysis.
tibble_solved_vs_unsolved_movies <- tibble_all_stats_movies %>% 
  mutate(outcome = ifelse(status == "solved" | status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)

# Remove the variables that don't make sense for unsolved vs. solved
final_solved_vs_unsolved_movies <- tibble_solved_vs_unsolved_movies %>% 
  select(-item_popularity, -genre_popularity, -item_age)

# All variables / Only movies.
logit_model_all_movies <- glm(outcome ~ OP_reply_count + full_post_length_words + thread_popularity + reply_counter + 
                               full_post_readability + total_unique_labels + total_labels + has_plot + plot_word_length + 
                               title_length_words + unique_user_count, 
                             data = final_solved_vs_unsolved_movies, na.action = na.exclude, family = "binomial")
summary(logit_model_all_movies)
tidy(logit_model_all_movies)
# performance::model_performance(logit_model_all_movies)
performance::model_performance(logit_model_all_movies) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()





### Logistic regression :: LLM-solved vs. LLM-unsolved :: Separate domains #####

# Make subsets of the data for analysis.
tibble_human_vs_llm_books <- tibble_all_stats_books %>% 
  filter(status != "unsolved") %>%
  mutate(outcome = ifelse(status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)

# Remove the variables that don't make sense for LLM-solved vs. LLM-unsolved
final_human_vs_llm_books <- tibble_human_vs_llm_books %>% 
  select(-unique_user_count, -OP_reply_count, -thread_popularity, -title_length_words, -reply_counter)

# All variables.
logit_model_all_llm_books <- glm(outcome ~ item_popularity + genre_popularity + full_post_length_words + total_unique_labels + 
                                   total_labels + has_plot + plot_word_length + item_age + full_post_readability, 
                                 data = final_human_vs_llm_books, na.action = na.exclude, family = "binomial")
summary(logit_model_all_llm_books)
tidy(logit_model_all_llm_books)
# performance::model_performance(logit_model_all_llm_books)
performance::model_performance(logit_model_all_llm_books) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()


# Make subsets of the data for analysis.
tibble_human_vs_llm_games <- tibble_all_stats_games %>% 
  filter(status != "unsolved") %>%
  mutate(outcome = ifelse(status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)

# Remove the variables that don't make sense for LLM-solved vs. LLM-unsolved
final_human_vs_llm_games <- tibble_human_vs_llm_games %>% 
  select(-unique_user_count, -OP_reply_count, -thread_popularity, -title_length_words, -reply_counter)

# All variables.
logit_model_all_llm_games <- glm(outcome ~ item_popularity + genre_popularity + full_post_length_words + total_unique_labels + 
                                   total_labels + has_plot + plot_word_length + item_age + full_post_readability, 
                                 data = final_human_vs_llm_games, na.action = na.exclude, family = "binomial")
summary(logit_model_all_llm_games)
tidy(logit_model_all_llm_games)
# performance::model_performance(logit_model_all_llm_games)
performance::model_performance(logit_model_all_llm_games) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()


# Make subsets of the data for analysis.
tibble_human_vs_llm_movies <- tibble_all_stats_movies %>% 
  filter(status != "unsolved") %>%
  mutate(outcome = ifelse(status == "llm-solved", 1, 0)) %>% 
  relocate(outcome, .after = "thread_id") %>% 
  select(-status)

# Remove the variables that don't make sense for LLM-solved vs. LLM-unsolved
final_human_vs_llm_movies <- tibble_human_vs_llm_movies %>% 
  select(-unique_user_count, -OP_reply_count, -thread_popularity, -title_length_words, -reply_counter)

# All variables.
logit_model_all_llm_movies <- glm(outcome ~ item_popularity + genre_popularity + full_post_length_words + total_unique_labels + 
                                   total_labels + has_plot + plot_word_length + item_age + full_post_readability, 
                                 data = final_human_vs_llm_movies, na.action = na.exclude, family = "binomial")
summary(logit_model_all_llm_movies)
tidy(logit_model_all_llm_movies)
# performance::model_performance(logit_model_all_llm_movies)
performance::model_performance(logit_model_all_llm_movies) %>% as_tibble() %>% mutate(output = glue("BIC = {round2(BIC)}")) %>% select(output) %>% pull()


