public class GenMissingBreakBug080 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "final";
            case 3:
                label = "draft";
                break;
            case 4:
                label = "paid";
                break;
            default:
                label = "active";
        }
        return label;
    }
}
