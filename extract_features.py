# extract_features.py
#
# Go through bidder data in the Kaggle Facebook recruiting competition IV and extract
# key information for classifying bidders as bots or humans.
#
# Date: 6/2/2015
# @author: Mike Gloudemans
#

import math
import operator
import sys

bids_file = "bids_labeled.csv"  # The original bids.csv file, modified to show whether each
                                # bid was placed by a robot, human, or unknown

def main(dataset = "train", minimum_time_threshold = 4000000000000000):

  # Initialize dictionaries to summarize attributes of auctions and bidders
  
  dBidders = {}                                        # bidder ->  all data on the bidder
  dWinners = {}                                        # auction -> bidder_id of winner
  dTotalBidsPerAuction = get_total_bids_per_auction()  # auction -> total bid count; TOTAL bids placed in ENTIRE auction
  dAuctionBidCounts = {}                               # auction -> running bid count; RUNNING TOTAL of bids placed in auction SO FAR 
  dResponseTimes = get_response_times(minimum_time_threshold)                
                                                       # bidder -> average time between competitor's bid and bidder's next bid
  dBiddingIntervals = get_own_bid_intervals(minimum_time_threshold)
                                                       # bidder -> average time between bidder's own bid and bidder's next bid
  dAverageCompetitors = get_average_competitors()      # bidder -> average number of participants in an auction that the bidder is in*
  dAverageBots = get_bots_per_auction()                # bidder -> average number of bots in an auction that the bidder is in*
  
  # *NOTE: (when actually outputting features, these two measurements are modified to show the average number of
  # OTHER competitors and bots in an auction that the bidder is in, excluding the bidder himself.
  
  # Get ID and class of each bidder
  with open("{}.csv".format(dataset)) as f:
    
    header = f.readline().strip().split(",")
    
    for line in f:
      data = line.strip().split(",")
      
      dBidders[data[0]] = {}
      
      for i in range(1,len(data)):
        dBidders[data[0]][header[i]] = data[i]

  # Get features for all bidders and export them to a CSV file.
  get_bidder_features(dBidders, dWinners, dTotalBidsPerAuction, dAuctionBidCounts, dResponseTimes, dBiddingIntervals, dAverageCompetitors, dAverageBots)
  write_bidder_features(dBidders, dWinners, dTotalBidsPerAuction, dAuctionBidCounts, dResponseTimes, dBiddingIntervals, dAverageCompetitors, dAverageBots, dataset)
  # Output all features to a file. A later module will offer the option to discard chosen features.
  
  print "Features extracted."
 
   
# Get features describing each of the bidders in dBidders,
# and store the features as keys under that bidder ID in dBidders.
def get_bidder_features(dBidders, dWinners, dTotalBidsPerAuction, dAuctionBidCounts, dResponseTimes, dBiddingIntervals, dAverageCompetitors, dAverageBots):
  with open(bids_file) as f:
    f.readline()
    for line in f:
      data = line.strip().split(",")
      bidder_id, auction = data[1], data[2]
      
      # Keep track of what point in each auction we're at, even
      # if we're not tracking this particular bidder.
      if auction in dAuctionBidCounts:
        dAuctionBidCounts[auction] += 1
      else:
        dAuctionBidCounts[auction] = 1
      
      # Increment bidder's bid count; if bidder not in bidder list
      if bidder_id in dBidders:
        if "total_bids" in dBidders[bidder_id]:
          dBidders[bidder_id]["total_bids"] += 1
        else:
          dBidders[bidder_id]["total_bids"] = 1
      else:
        # If bidder not in bidder list, there's no information we
        # need here; move on.
        continue
      
      # Record times of first and last bids posted
      if "first_bid" not in dBidders[bidder_id]:
        dBidders[bidder_id]["first_bid"] = float(data[5]) / 1000000000000000
      else: 
        dBidders[bidder_id]["first_bid"] = min(dBidders[bidder_id]["first_bid"], float(data[5]) / 1000000000000000)
        
      if "last_bid" not in dBidders[bidder_id]:
        dBidders[bidder_id]["last_bid"] = float(data[5]) / 1000000000000000
      else:
        dBidders[bidder_id]["last_bid"] = max(dBidders[bidder_id]["last_bid"], float(data[5]) / 1000000000000000)
  
      # Track list of different auctions bidder has participated in
      auction = data[2]
      if "auctions" in dBidders[bidder_id]:
        dBidders[bidder_id]["auctions"].add(auction)
      else:
        dBidders[bidder_id]["auctions"] = set([auction])
  
      # Track number of different countries bidder has bid in
      country = data[6]
      if "countries" in dBidders[bidder_id]:
        dBidders[bidder_id]["countries"].add(country)
      else:
        dBidders[bidder_id]["countries"] = set([country])
        
      # Track number of different IPs bidder has placed bids from
      ip = data[7]
      if "ips" in dBidders[bidder_id]:
        dBidders[bidder_id]["ips"].add(ip)
      else:
        dBidders[bidder_id]["ips"] = set([ip])  
       
      # Track number of different URLs bidder has placed bids from
      url = data[8]
      if "urls" in dBidders[bidder_id]:
        dBidders[bidder_id]["urls"].add(url)
      else:
        dBidders[bidder_id]["urls"] = set([url])
        
      # Track number of different devices bidder has placed bids from
      device = data[4]
      if "devices" in dBidders[bidder_id]:
        dBidders[bidder_id]["devices"].add(device)
      else:
        dBidders[bidder_id]["devices"] = set([device])
        
      # Update winners dictionary to reflect last bidder.
      # NOTE: This approach might be flawed if there are auctions spanning the time gaps in the bid file.
      # For now I'm assuming all auctions are shorter than that whole time period.
      dWinners[auction] = bidder_id
      
      # Figure out what part of the auction (order of bids) this bidder tends to bid in most often
      # Possible idea: replace this using time data rather than bid order data
      if "bidding_stage" in dBidders[bidder_id]:
        if dTotalBidsPerAuction[auction] == 1:
          dBidders[bidder_id]["bidding_stage"] += 0.5
        else:
          dBidders[bidder_id]["bidding_stage"] += (dAuctionBidCounts[auction] - 1 * 1.0) / (dTotalBidsPerAuction[auction] - 1)
      else:
        if dTotalBidsPerAuction[auction] == 1:
          dBidders[bidder_id]["bidding_stage"] = 0.5
        else:
          dBidders[bidder_id]["bidding_stage"] = (dAuctionBidCounts[auction] - 1 * 1.0) / (dTotalBidsPerAuction[auction] - 1)

  # Find fraction of bids placed by each bidder within auctions of participation
  for bidder in dBidders.keys():
    total_bids_in_auctions = 0
    if "auctions" in dBidders[bidder]:
      for auction in dBidders[bidder]["auctions"]:
        total_bids_in_auctions += dTotalBidsPerAuction[auction]
      dBidders[bidder]["bid_percent"] = dBidders[bidder]["total_bids"] * 1.0 / total_bids_in_auctions          

      
  for bidder in dBidders.keys():
    if not "auctions" in dBidders[bidder]:
    
      # If bidder has not placed a single bid, we'll just make up some "average" data
      # for the bidder and probably exclude the bidder from testing later.
    
      dBidders[bidder]["countries"] = 0
      dBidders[bidder]["urls"] = 0
      dBidders[bidder]["ips"] = 0
      dBidders[bidder]["devices"] = 0
      dBidders[bidder]["total_bids"] = 0
      dBidders[bidder]["auctions"] = 0
      dBidders[bidder]["merchandise"] = -1
      dBidders[bidder]["bidding_stage"] = 0.5
      dBidders[bidder]["bid_percent"] = 0
      dBidders[bidder]["first_bid"] = 9.760241 # Not sure about these ones....
      dBidders[bidder]["last_bid"] = 9.763003
      dAverageCompetitors[bidder] = 200
      dAverageBots[bidder] = 6
      
    else:
      dBidders[bidder]["countries"] = len(dBidders[bidder]["countries"]) 
      dBidders[bidder]["urls"] = len(dBidders[bidder]["urls"])
      dBidders[bidder]["ips"] = len(dBidders[bidder]["ips"])
      dBidders[bidder]["devices"] = len(dBidders[bidder]["devices"])
      dBidders[bidder]["auctions"] = len(dBidders[bidder]["auctions"])
      dBidders[bidder]["bidding_stage"] = dBidders[bidder]["bidding_stage"] / dBidders[bidder]["total_bids"]
      
    if not bidder in dResponseTimes:
      dResponseTimes[bidder] = (20000000000L, 0)
    if not bidder in dBiddingIntervals:
      dBiddingIntervals[bidder] = (1000000000000L, 0)
      

  # Count up total number of auctions won by each bidder
  dWins = {}
  for auction in dWinners:
    if dWinners[auction] in dWins:
      dWins[dWinners[auction]] += 1
    else:
      dWins[dWinners[auction]] = 1
 
  # Compute percent of auctions won by each bidder
  for bidder in dBidders:
    if bidder in dWins:
      dBidders[bidder]["wins"] = dWins[bidder]
      if dBidders[bidder]["auctions"] != 0:
        dBidders[bidder]["win_rate"] = dWins[bidder] * 1.0 / dBidders[bidder]["auctions"]
      else:
        dBidders[bidder]["win_rate"] = 0.0
    else:
      dBidders[bidder]["wins"] = 0
      dBidders[bidder]["win_rate"] = 0.0
 
 
# Write features describing each of the bidders to a file 
def write_bidder_features(dBidders, dWinners, dTotalBidsPerAuction, dAuctionBidCounts, dResponseTimes, dBiddingIntervals, dAverageCompetitors, dAverageBots, dataset):
  with open("{}_features.csv".format(dataset), "wb") as w:
  
    # Display header
    w.write("bidder_id,total_bids,auctions,countries,ips,urls,devices,win_rate,wins,bids_per_auction,bid_percent,bidding_stage,response_time,bid_interval,first_bid,last_bid,competitors,average_bots,outcome\n")
    
    # Print columns as CSV in accordance with header
    for bidder in dBidders.keys():
      data = []
      data.append(bidder)
      data.append(math.log(dBidders[bidder]["total_bids"] + 1))
      data.append(math.log(dBidders[bidder]["auctions"] + 1))
      data.append(math.log(dBidders[bidder]["countries"] + 1))
      data.append(math.log(dBidders[bidder]["ips"] + 1))
      data.append(math.log(dBidders[bidder]["urls"] + 1))
      data.append(math.log(dBidders[bidder]["devices"] + 1))
      data.append(dBidders[bidder]["win_rate"])
      data.append(math.log(dBidders[bidder]["wins"] + 1))
      if dBidders[bidder]["auctions"] == 0:
        data.append(0)
      else:
        data.append(dBidders[bidder]["total_bids"] * 1.0 / dBidders[bidder]["auctions"])
      data.append(dBidders[bidder]["bid_percent"])
      data.append(dBidders[bidder]["bidding_stage"])
      data.append(dResponseTimes[bidder][0]/ 10000000000)
      data.append(dBiddingIntervals[bidder][0] / 10000000000)
      data.append((dBidders[bidder]["first_bid"] - 9.76) * 10)
      data.append((dBidders[bidder]["last_bid"] - 9.76) * 10)
      
      data.append(dAverageCompetitors[bidder])
      
      if dataset == "train" and dBidders[bidder]["outcome"] == 1:
          data.append(((dAverageBots[bidder] * dBidders[bidder]["auctions"]) - dBidders[bidder]["auctions"]) / dBidders[bidder]["auctions"])
      else:
        data.append(dAverageBots[bidder])
        
      if dataset == "train":
        data.append(dBidders[bidder]["outcome"])
      
      w.write(",".join([str(d) for d in data]) + "\n")
  
   
# Outputs dictionary of {bidder ID -> average time delay between last opponent bid and own bid}
def get_response_times(minimum_time_threshold):
  with open(bids_file) as f:
    f.readline()
    
    dLastBids = {}            # Running list of last bid placed in each auction
    dAverageResponse = {}     # Running list of each bidder's average response times
    
    for line in f:
      data = line.strip().split(",")
      bidder_id, auction, time = data[1], data[2], int(data[5])

      if auction in dLastBids:
        elapsed = time - dLastBids[auction]
        
        # The bids.csv file has a few jumps, so don't count the elapsed time
        # if we've just been through one of these jumps.
        
        if abs(elapsed) > minimum_time_threshold:
          dLastBids[auction] = time
          continue          
        
        if bidder_id in dAverageResponse:
          avg = dAverageResponse[bidder_id]
          
          total_response = avg[0] * avg[1]
          new_avg = ((total_response + elapsed) / (avg[1] + 1), avg[1] + 1)
          dAverageResponse[bidder_id] = new_avg
          
        else:
          dAverageResponse[bidder_id] = (elapsed, 1)
        
        dLastBids[auction] = time
        
      else:
        dLastBids[auction] = time
        
  return dAverageResponse


# Outputs dictionary of {bidder ID -> average time between own bids in same auction}
def get_own_bid_intervals(minimum_time_threshold):
  with open(bids_file) as f:
    f.readline()
    
    dLastBids = {}
    dAverageResponse = {}

    for line in f:
      data = line.strip().split(",")
      bidder_id, time = data[1], int(data[5])
      
      if bidder_id in dLastBids:
        elapsed = time - dLastBids[bidder_id]
        
        # The bids.csv file has a few jumps, so don't count the elapsed time
        # if we've just been through one of these jumps.
        
        if abs(elapsed) > minimum_time_threshold:
          dLastBids[bidder_id] = time
          continue          

        if bidder_id in dAverageResponse:
          avg = dAverageResponse[bidder_id]
          
          total_response = avg[0] * avg[1]
          new_avg = ((total_response + elapsed) / (avg[1] + 1), avg[1] + 1)
          dAverageResponse[bidder_id] = new_avg
          
        else:
          dAverageResponse[bidder_id] = (elapsed, 1)
        
        dLastBids[bidder_id] = time
        
      else:
        dLastBids[bidder_id] = time
        
  return dAverageResponse  

  
# Get number of competitors for bidder's auctions
def get_average_competitors():

  # Make a list of all the participants in each auction
  with open(bids_file) as f:
    f.readline()
    
    dAuctions = {}
    for line in f:
      data = line.strip().split(",")
      bidder_id, auction = data[1], data[2]
      
      if auction in dAuctions:
        dAuctions[auction].add(bidder_id)
      else:
        dAuctions[auction] = set([bidder_id])
        
    for key in dAuctions:
      dAuctions[key] = len(dAuctions[key])
      
  dParticipation = {}
  dCompetitors = {}
  
  # Determine average number of participants in each bidder's auctions
  with open(bids_file) as f:
    f.readline()
    
    for line in f:
      data = line.strip().split(",")
      auction = data[2]
      bidder_id = data[1] 
 
      if bidder_id not in dParticipation:
        dParticipation[bidder_id] = set([])
        dCompetitors[bidder_id] = 0
        
      if auction not in dParticipation[bidder_id]:
        dCompetitors[bidder_id] += dAuctions[auction]
        dParticipation[bidder_id].add(auction)
      
  for key in dCompetitors:
    dCompetitors[key] = dCompetitors[key] * 1.0 / len(dParticipation[key])
      
  return dCompetitors
 
 
# Outputs dictionary of {bidder ID -> # bots in that bidder's auctions}
def get_bots_per_auction():

  # Make a list of participants in each auction and determine how many are bots.
  with open(bids_file) as f:
    f.readline()
    
    dParticipation = {}
    dBots = {}              # Number of known bots bidding in each auction
    
    for line in f:
      data = line.strip().split(",")
      bidder_id, auction, outcome = data[1], data[2], int(data[9]) 
      
      if auction not in dParticipation:
        dParticipation[auction] = set([])
        dBots[auction] = 0
      
      if outcome == 1 and bidder_id not in dParticipation[auction]:
        dParticipation[auction].add(bidder_id)
        dBots[auction] += 1
      
  dParticipation = {}
  dAverageBots = {}
  
  # Figure out average number of bots in each bidder's auction list
  with open(bids_file) as f:
    f.readline()
    
    for line in f:
      data = line.strip().split(",")
      auction = data[2]
      bidder_id = data[1]

      if bidder_id not in dParticipation:
        dParticipation[bidder_id] = set([])
        dAverageBots[bidder_id] = 0
        
      if auction not in dParticipation[bidder_id]:
        dParticipation[bidder_id].add(auction)
        dAverageBots[bidder_id] += dBots[auction]
    
  for key in dAverageBots.keys():
    dAverageBots[key] = dAverageBots[key] * 1.0 / len(dParticipation[key])
    
  return dAverageBots
  
  
# Outputs dictionary of {auction ID -> # bids placed in auction}
def get_total_bids_per_auction():
  dTotalBidsPerAuction = {}
  
  with open(bids_file) as f:
    f.readline()
    
    for line in f:
      data = line.strip().split(",")
      
      auction = data[2]      
      if auction in dTotalBidsPerAuction:
        dTotalBidsPerAuction[auction] += 1
      else:
        dTotalBidsPerAuction[auction] = 1
        
  return dTotalBidsPerAuction

  

    
if __name__ == "__main__":
  main(dataset = "train")


