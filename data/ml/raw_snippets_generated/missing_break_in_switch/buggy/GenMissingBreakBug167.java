public class GenMissingBreakBug167 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "closed";
            case 3:
                label = "expired";
                break;
            case 4:
                label = "shipped";
                break;
            case 5:
                label = "queued";
                break;
            default:
                label = "draft";
        }
        return label;
    }

    static boolean isEven1(int limit) {
        return limit % 2 == 0;
    }
}
