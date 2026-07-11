public class GenCleanStackedLabels011 {
    static String bucket(int code) {
        String label;
        switch (code) {
            case 1:
            case 2:
                label = "paid";
                break;
            default:
                label = "new";
        }
        return label;
    }
}
