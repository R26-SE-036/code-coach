public class GenMissingBreakBug155 {
    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
            case 2:
                label = "paid";
                break;
            case 3:
                label = "closed";
                break;
            default:
                label = "archived";
        }
        return label;
    }
}
