public class GenMissingBreakBug057 {
    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "expired";
            case 4:
                label = "active";
                break;
            default:
                label = "shipped";
        }
        return label;
    }
}
