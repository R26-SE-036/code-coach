public class GenMissingBreakBug076 {
    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "queued";
            case 4:
                label = "shipped";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
