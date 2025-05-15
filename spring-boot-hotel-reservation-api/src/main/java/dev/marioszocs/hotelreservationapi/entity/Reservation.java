package dev.marioszocs.hotelreservationapi.entity;

import lombok.*;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

/**
 * Entity representing a hotel reservation.
 */
@Getter
@Setter
@Entity
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Table(name = "reservation")
public class Reservation extends AuditableEntity {

    /**
     * ID of the hotel where the reservation is made.
     */
    @Column(name = "hotel_id", nullable = false)
    private Integer hotelId;

    /**
     * Check-in date in ISO format (yyyy-MM-dd).
     */
    @Column(name = "check_in", nullable = false)
    private String checkIn;

    /**
     * Check-out date in ISO format (yyyy-MM-dd).
     */
    @Column(name = "check_out", nullable = false)
    private String checkOut;

    /**
     * Number of guests included in the reservation.
     * Must be between 1 and 8.
     */
    @Min(1)
    @Max(8)
    @Column(nullable = false)
    private Integer guests;

    /**
     * Status of the reservation (e.g., confirmed, canceled).
     */
    @Column
    private boolean status;
}
