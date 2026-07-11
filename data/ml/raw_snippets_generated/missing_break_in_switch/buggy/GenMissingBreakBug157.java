public class GenMissingBreakBug157 {
    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
            case 2:
                label = "new";
                break;
            case 3:
                label = "queued";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
