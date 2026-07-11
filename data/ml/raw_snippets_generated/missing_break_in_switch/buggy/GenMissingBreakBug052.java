public class GenMissingBreakBug052 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "queued";
            case 3:
                label = "active";
                break;
            case 4:
                label = "draft";
                break;
            case 5:
                label = "final";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
