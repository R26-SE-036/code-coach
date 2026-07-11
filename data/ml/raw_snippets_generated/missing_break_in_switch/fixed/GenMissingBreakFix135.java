public class GenMissingBreakFix135 {
    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "final";
                break;
            case 3:
                label = "archived";
                break;
            case 4:
                label = "queued";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
