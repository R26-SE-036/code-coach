public class GenMissingBreakBug051 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "new";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "final";
            case 5:
                label = "shipped";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
