public class GenMissingBreakFix036 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "expired";
                break;
            case 2:
                label = "closed";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "shipped";
                break;
            case 5:
                label = "queued";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
