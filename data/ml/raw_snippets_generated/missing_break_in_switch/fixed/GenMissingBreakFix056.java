public class GenMissingBreakFix056 {
    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "final";
                break;
            case 2:
                label = "expired";
                break;
            case 3:
                label = "paid";
                break;
            case 4:
                label = "queued";
                break;
            case 5:
                label = "closed";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
