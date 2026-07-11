public class GenMissingBreakFix093 {
    static String describeInvoice(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "active";
                break;
            case 3:
                label = "archived";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
