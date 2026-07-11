public class GenMissingBreakFix169 {
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
                break;
            case 4:
                label = "final";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
