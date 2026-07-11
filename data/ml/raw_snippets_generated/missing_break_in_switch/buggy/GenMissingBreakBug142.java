public class GenMissingBreakBug142 {
    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "paid";
            case 2:
                label = "final";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "draft";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
