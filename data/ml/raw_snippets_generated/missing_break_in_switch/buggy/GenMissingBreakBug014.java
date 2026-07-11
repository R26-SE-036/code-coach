public class GenMissingBreakBug014 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "new";
            case 4:
                label = "final";
                break;
            case 5:
                label = "active";
                break;
            default:
                label = "queued";
        }
        return label;
    }
}
