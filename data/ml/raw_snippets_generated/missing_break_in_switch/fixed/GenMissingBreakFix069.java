public class GenMissingBreakFix069 {
    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "shipped";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
