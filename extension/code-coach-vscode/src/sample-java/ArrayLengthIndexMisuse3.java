public class ArrayLengthIndexMisuse3 {
    static double getLatestPrice(double[] prices) {
        return prices[prices.length];
    }

    public static void main(String[] args) {
        double[] prices = { 9.99, 14.49, 22.00, 5.50 };
        System.out.println("Latest price: " + getLatestPrice(prices));
    }
}
