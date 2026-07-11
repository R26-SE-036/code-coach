public class GenMissingBreakFix129 {
    static String describeReport(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "closed";
                break;
            case 4:
                label = "draft";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
