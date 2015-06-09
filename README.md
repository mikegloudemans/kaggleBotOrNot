# kaggleBotOrNot
This was my entry for the June 2015 Kaggle contest "Facebook Recruiting IV: Human or Robot?" My model achieved a final AUC of 0.93361 and earned 50th place out of 1004 on the Private Leaderboard.

I used the RandomForestClassifier from Python's sklearn with the default settings, except for n_estimators = 500. I then
computed bot probabilities independently with a LogisticRegression classifier and mixed the results of the two models for
my final prediction. I found that a mix of 80% RandomForestClassifer and 20% LogisticRegression was ideal.

Based on my own experience and the comments by other competitors, the biggest challenge in this contest was selecting
informative features. My goal was to keep the model simple, with as few features as possible so as to avoid overfitting.
My final model included the following features for each bidder:
  - total number of bids placed (log)
  - total number of auctions of participation (log)
  - total number of countries from which bids were placed (log)
  - total number of ips from which bids were placed (log)
  - total number of urls from which bids were placed (log)
  - total number of device types from which bids were placed (log)
  - total number of "wins" (last bid placed in auction) (log)
  - win percent
  - mean bids per auction
  - bidding stage (whether bids were placed earlier or later in auction)
  - mean time between own bids
  - mean time between own bid and the previous bid placed by a competitor
  - mean number of competitors per auction of participation
  - mean number of bots per auction of participation (not including self)
  
The features related to the progress of the auction (number of wins, bidding stage) may not have actually been useful since it's
difficult to say whether an auction was truly completed by the end of the traning data.

I also experimented with several other features, which did not seem to be as useful so I removed them from my final classifier: 
  - merchandise category
  - number of bids placed in each specific country (only including countries with >50 different bidders)
  - time of first bid
  - time of last bid
  - percentage of all bids placed in auctions of participation
  
One potentially useful feature that I neglected to test was the time distribution of the bids. Some of the top entries in the
contest seem to have taken advantage of the fact that human bidders bid at certain times of day more often, while bots might
bid at any time of day.

To run the code, I first modified the original "bids.csv" file to produce a "bids_labeled.csv" file with an additional column labeling all bids
as 0 for human, 1 for bot, or 2 for unknown. Then I ran "extract_features.py" followed by "apply_model.py".

I enjoyed the contest and look forward to trying some more of these contests in the future!
