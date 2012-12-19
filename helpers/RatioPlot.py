
import sys

def DrawRatioPlot(request, mcList, denom_pair):

    denom = denom_pair[1]

    if len( mcList ) == 0:
        print "Error: No numerator hists provided"
        raise Exception("RatioPlot")
        return

    # Get the total MC
    #(templateName, templateHist) = mcList[0]
    #numerator = templateHist.Clone(templateName + "_numerator")
    #for (name, hist) in mcList[1:]:
    #    denominator.Add(hist)

    # Get the Ratio
    ratio_list = []

    default = denom.Clone(denom.GetName() + "_default_ratio")        
    for bin_idx in range(default.GetNbinsX()):
        default.SetBinContent(bin_idx+1, 1.0)
    default.SetLineColor(1)
    default.SetMarkerStyle(0)
    #default.Draw("HIST")
    default.GetYaxis().SetLabelSize(.15)
    default.GetYaxis().SetNdivisions(5)
    ratio_list.append(default)

    ratio_min = sys.float_info.max
    ratio_max = 0.0

    for (name, hist) in mcList:
        ratio = hist.Clone(hist.GetName() + "_ratio")        
        ratio.Divide(denom)
        ratio_min = min(ratio_min, ratio.GetMinimum())
        ratio_max = max(ratio_max, ratio.GetMaximum())
        #ratio.SetAxisRange( 0, 2, "Y" )

        for bin_idx in range(denom.GetNbinsX()):
            if denom.GetBinContent(bin_idx+1) < .00001 \
                    and denom.GetBinContent(bin_idx+1) < .00001:
                ratio.SetBinContent(bin_idx+1, 1.0)
                #print "Setting 0/0 content to 1.0"

        ratio.SetMarkerStyle(0)
        #ratio.Draw("HISTSAME")
        ratio_list.append(ratio)

    ratio_min = 0.0
    ratio_max = max(1.2*ratio_max, 2.0)
    default.SetAxisRange(ratio_min, ratio_max, "Y")
    default.Draw("HIST")
    for hist in ratio_list[1:]:
        hist.Draw("HISTSAME")

    default.Draw("HISTSAME")

    return ratio_list
