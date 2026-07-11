public class GenMissingBreakBug086 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "expired";
                break;
            default:
                label = "new";
        }
        return label;
    }

    static String describeAccount(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "queued";
                break;
            case 2:
                label = "archived";
            case 3:
                label = "paid";
                break;
            case 4:
                label = "shipped";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
