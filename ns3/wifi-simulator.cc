/* -*- Mode:C++; c-file-style:"gnu"; indent-tabs-mode:nil; -*- */
/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/mobility-module.h"
#include "ns3/wifi-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"
#include "ns3/flow-monitor-module.h"

using namespace ns3;
using namespace std;

NS_LOG_COMPONENT_DEFINE ("WiFiSpeedSTA");

int
main (int argc, char *argv[])
{
  /* Set experiment information */
  string experiment ("wifi-speed-sta-test");
  string strategy ("wifi-default");

  /* Get command line parameters */
  CommandLine cmd;
  double simulationTime = 10.0;
  cmd.AddValue ("time", "The simulation time.", simulationTime);
  uint32_t staCount = 1;
  cmd.AddValue ("stas", "The amount of STA's to create.", staCount);
  uint32_t runNumber = 1;
  cmd.AddValue ("run", "The number of this run.", runNumber);
  string outputFilename = "data.csv";
  cmd.AddValue ("of", "The output file for the data.", outputFilename);
  string dataRate = "5Mbps";
  cmd.AddValue ("dr", "The datarate from STA's -> AP", dataRate);
  uint32_t packetSize = 1024;
  cmd.AddValue ("ps", "The packet size used to send packets", packetSize);
  cmd.Parse (argc, argv);

  /* Make sure the simulation is random */
  time_t timev;
  time(&timev);
  RngSeedManager::SetSeed (timev);
  RngSeedManager::SetRun (runNumber);

  /* Create output file */
  std::ofstream outputStream (outputFilename.c_str (), ios::app);

  /* First create the nodes */
  NS_LOG_INFO ("Creating nodes.");
  Ptr<Node> apNode = CreateObject<Node> ();
  NodeContainer staNodes;
  staNodes.Create (staCount);

  /* Create WiFi and Internet stack */
  NS_LOG_INFO ("Installing WiFi and Internet stack.");
  WifiHelper wifi;
  wifi.SetStandard (WIFI_PHY_STANDARD_80211b); // Set to 802.11b

  YansWifiPhyHelper wifiPhy = YansWifiPhyHelper::Default ();
  wifiPhy.Set ("RxGain", DoubleValue (0));
  wifiPhy.SetPcapDataLinkType (YansWifiPhyHelper::DLT_IEEE802_11_RADIO);

  YansWifiChannelHelper wifiChannel = YansWifiChannelHelper::Default ();
  wifiChannel.SetPropagationDelay ("ns3::ConstantSpeedPropagationDelayModel");
  wifiChannel.AddPropagationLoss ("ns3::FixedRssLossModel", "Rss", DoubleValue (-80));
  wifiPhy.SetChannel (wifiChannel.Create ());

  NqosWifiMacHelper wifiMac = NqosWifiMacHelper::Default ();
  wifi.SetRemoteStationManager ("ns3::ConstantRateWifiManager",
                                "DataMode", StringValue ("DsssRate11Mbps"),
                                "ControlMode", StringValue ("DsssRate11Mbps"));

  Ssid ssid = Ssid ("ns3-80211b");
  // Setup STA's
  wifiMac.SetType ("ns3::StaWifiMac",
                   "Ssid", SsidValue (ssid),
                   "ActiveProbing", BooleanValue (false));
  NetDeviceContainer staDevices = wifi.Install (wifiPhy, wifiMac, staNodes);

  // Setup AP
  wifiMac.SetType ("ns3::ApWifiMac",
                   "Ssid", SsidValue (ssid));
  NetDeviceContainer apDevice = wifi.Install (wifiPhy, wifiMac, apNode);

  /* Setup mobility */
  NS_LOG_INFO ("Defining mobility.");
  MobilityHelper mobility;
  Ptr<ListPositionAllocator> positionAlloc = CreateObject<ListPositionAllocator> ();

  positionAlloc->Add (Vector (0.0, 0.0, 3.0));
  for(uint16_t i = 0; i < staCount; i++)
	  positionAlloc->Add (Vector (3.0, 3.0, 0.0));

  mobility.SetPositionAllocator (positionAlloc);
  mobility.SetMobilityModel ("ns3::ConstantPositionMobilityModel");
  mobility.Install (apNode);
  mobility.Install (staNodes);


  /* Create Network */
  NS_LOG_INFO ("Create network and assign IP addresses.");
  InternetStackHelper internet;
  internet.Install (apNode);
  internet.Install (staNodes);
  Ipv4AddressHelper ipAddrs;
  ipAddrs.SetBase ("192.168.0.0", "255.255.255.0");
  Ipv4InterfaceContainer apIp = ipAddrs.Assign (apDevice);
  Ipv4InterfaceContainer stasIp = ipAddrs.Assign (staDevices);

  /* Create traffic from STA's to AP */
  NS_LOG_INFO("Create traffic from STA's to AP.");
  for(uint16_t i = 0; i < staCount; i++) {
	  uint16_t port = 8000 + i;
	  Address staAddress (InetSocketAddress (stasIp.GetAddress (i), port));
	  Address apAddress (InetSocketAddress (apIp.GetAddress (0), port));

	  // Create the access point application to receive packets
	  PacketSinkHelper apSink ("ns3::TcpSocketFactory", apAddress);
	  ApplicationContainer apApp = apSink.Install (apNode);
	  apApp.Start (Seconds (0));
	  apApp.Stop (Seconds (simulationTime + 1));

	  // Create the STA application to send packets
	  OnOffHelper staOnOff ("ns3::TcpSocketFactory", staAddress);
	  staOnOff.SetAttribute ("OnTime",  StringValue ("ns3::ConstantRandomVariable[Constant=1]"));
	  staOnOff.SetAttribute ("OffTime", StringValue ("ns3::ConstantRandomVariable[Constant=0]"));
	  staOnOff.SetAttribute ("PacketSize", UintegerValue (packetSize));
	  staOnOff.SetAttribute ("DataRate", StringValue (dataRate));
	  staOnOff.SetAttribute ("Remote", AddressValue (apAddress));

	  ApplicationContainer staApp = staOnOff.Install (staNodes.Get (i));
	  staApp.Start (Seconds (1));
	  staApp.Stop (Seconds (simulationTime + 1));
  }

  /* Setup flow monitor */
  NS_LOG_INFO ("Setup flow monitor.");
  FlowMonitorHelper flowHelper;
  Ptr<FlowMonitor> flowMonitor = flowHelper.InstallAll ();

  /* Run the simulation */
  NS_LOG_INFO ("Start simulation.");
  Simulator::Stop (Seconds(simulationTime));
  Simulator::Run ();
  NS_LOG_INFO ("Done running simulation.");

  /* Generate statistics */
  NS_LOG_INFO ("Generate statistics.");
  double throughputSum = 0;
  double throughputSumSq = 0;

  flowMonitor->CheckForLostPackets ();
  Ptr<Ipv4FlowClassifier> classifier = DynamicCast<Ipv4FlowClassifier> (flowHelper.GetClassifier ());
  std::map<FlowId, FlowMonitor::FlowStats> stats = flowMonitor->GetFlowStats ();
  for (std::map<FlowId, FlowMonitor::FlowStats>::const_iterator i = stats.begin (); i != stats.end (); ++i)
  {
	  Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow (i->first);
	  if (t.sourceAddress == apIp.GetAddress(0))
		  continue;

	  float throughput = i->second.rxBytes * 8.0 / simulationTime / 1024 / 1024;
	  throughputSum += throughput;
	  throughputSumSq += powf(throughput, 2);

	  std::cout << "Flow " << i->first << " (" << t.sourceAddress << " -> " << t.destinationAddress << ")" << endl;
	  std::cout << "  Tx Bytes:   " << i->second.txBytes << endl;
	  std::cout << "  Rx Bytes:   " << i->second.rxBytes << endl;
	  std::cout << "  Throughput: " << throughput << " Mbps" << endl;
	  std::cout << "  Delay average: " << i->second.delaySum.GetMicroSeconds () / i->second.rxPackets << " us" << endl;
  }

  double throughputMean = throughputSum / staCount;
  double throughputVariance = (throughputSumSq - (powf(throughputSum, 2) / staCount)) / staCount;
  double troughputStd = sqrtf(throughputVariance);
  std::cout << "Overview:\n";
  std::cout << "  Time:   " << simulationTime << endl;
  outputStream << simulationTime << ",";
  std::cout << "  STA count:   " << staCount << endl;
  outputStream << staCount << ",";
  std::cout << "  Throughput sum:     " << throughputSum << endl;
  outputStream << throughputSum << ",";
  std::cout << "  Throughput mean:     " << throughputMean << endl;
  outputStream << throughputMean << ",";
  std::cout << "  Throughput variance: " << throughputVariance << endl;
  outputStream << throughputVariance << ",";
  std::cout << "  Throughput std:      " << troughputStd << endl;
  outputStream << troughputStd << endl;

  /* Destroy the simulation and close data file */
  outputStream.close ();
  Simulator::Destroy ();
  NS_LOG_INFO ("Destroyed.");
  return 0;
}
