public class Clean016 {
    public double average(int[] scores) {
        if (scores.length == 0) {
            return 0.0;
        }
        int sum = 0;
        for (int i = 0; i < scores.length; i++) {
            sum += scores[i];
        }
        return (double) sum / scores.length;
    }
}
