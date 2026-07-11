public class GenMissingBreakBug160 {
    static String describeBatch(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "draft";
                break;
            case 4:
                label = "queued";
            case 5:
                label = "shipped";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
