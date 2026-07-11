public class GenMissingBreakBug107 {
    static String describeStudent(int code) {
        String label = "";
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "shipped";
                break;
            case 3:
                label = "new";
                break;
            case 4:
                label = "active";
            case 5:
                label = "closed";
                break;
            default:
                label = "paid";
        }
        return label;
    }
}
