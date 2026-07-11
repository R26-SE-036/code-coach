public class GenMissingBreakBug169 {
    static String describeOrder(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "archived";
                break;
            case 3:
                label = "queued";
            case 4:
                label = "final";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
